from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_DECIMALS,
    DEFAULT_METRIC,
    DEFAULT_MODEL,
    DEFAULT_TOP_K,
    EMBEDDING_COLUMN_PREFIX,
    MODEL_REGISTRY,
    resolve_model,
    suggest_model_for_column,
)
from .embed import generate_embeddings, load_model
from .io import read_xlsx, write_xlsx
from .neighbors import find_neighbors
from .visuals import completion_panel, format_elapsed, show_file_table, spinner_phase

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")
AUTO_KEY_COLUMN = "_row_id"


@dataclass
class ColumnInfo:
    name: str
    index: int
    dtype: str
    unique_count: int
    total_count: int
    null_count: int
    is_likely_key: bool
    is_likely_text: bool
    suggested_model: str


def inspect_columns(df: pd.DataFrame) -> list[ColumnInfo]:
    total = len(df)
    result: list[ColumnInfo] = []
    for i, col in enumerate(df.columns, 1):
        series = df[col]
        null_count = int(series.isna().sum())
        unique_count = int(series.nunique())
        dtype = _classify_dtype(series)
        is_likely_key = unique_count == total and null_count == 0
        is_likely_text = dtype in ("text", "category")
        suggested_model = suggest_model_for_column(col)
        result.append(
            ColumnInfo(
                name=col,
                index=i,
                dtype=dtype,
                unique_count=unique_count,
                total_count=total,
                null_count=null_count,
                is_likely_key=is_likely_key,
                is_likely_text=is_likely_text,
                suggested_model=suggested_model,
            )
        )
    return result


def _classify_dtype(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    sample = series.dropna().head(100).astype(str)
    if sample.empty:
        return "mixed"
    avg_len = sample.str.len().mean()
    if avg_len > 20:
        return "text"
    if series.nunique() < len(series) * 0.5:
        return "category"
    return "text"


def ensure_dirs() -> None:
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)


def scan_input_files() -> list[Path]:
    if not INPUT_DIR.exists():
        return []
    return sorted(p for p in INPUT_DIR.glob("*.xlsx") if not p.name.startswith("~"))


def read_file_info(path: Path) -> tuple[int, int]:
    try:
        df = pd.read_excel(path, engine="openpyxl", nrows=0)
        full_df = pd.read_excel(path, engine="openpyxl")
        return len(full_df), len(df.columns)
    except Exception:
        return 0, 0


def prompt_choice(console: Console, label: str, min_val: int, max_val: int) -> int:
    while True:
        try:
            raw = input(f"  {label} [{min_val}-{max_val}]: ").strip()
            if not raw:
                continue
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            console.print(f"  [red]Please enter a number between {min_val} and {max_val}.[/red]")
        except ValueError:
            console.print(f"  [red]Please enter a number between {min_val} and {max_val}.[/red]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [yellow]Cancelled.[/yellow]")
            raise SystemExit(0) from None


def prompt_multi_choice(console: Console, label: str, max_val: int) -> list[int]:
    while True:
        try:
            raw = input(f"  {label} [1-{max_val}, comma-separated]: ").strip()
            vals = [int(v.strip()) for v in raw.split(",") if v.strip()]
            if all(1 <= v <= max_val for v in vals) and vals:
                return vals
            console.print(f"  [red]Enter numbers between 1 and {max_val}, comma-separated.[/red]")
        except ValueError:
            console.print(f"  [red]Enter numbers between 1 and {max_val}, comma-separated.[/red]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [yellow]Cancelled.[/yellow]")
            raise SystemExit(0) from None


def prompt_optional(console: Console, label: str, default: str = "") -> str:
    try:
        raw = input(f"  {label} [{default}]: ").strip()
        return raw if raw else default
    except (EOFError, KeyboardInterrupt):
        console.print("\n  [yellow]Cancelled.[/yellow]")
        raise SystemExit(0) from None


def show_columns(console: Console, columns: list[ColumnInfo]) -> None:
    table = Table(show_header=True, header_style="bold", pad_edge=False, show_lines=False)
    table.add_column("#", style="bold", width=4)
    table.add_column("Column")
    table.add_column("Type", width=10)
    table.add_column("Info")
    table.add_column("Suggested Model", style="cyan", width=14)

    for col in columns:
        if col.is_likely_key:
            info = f"{col.unique_count} unique"
        elif col.is_likely_text or col.dtype == "text":
            info = "text"
        elif col.dtype == "numeric":
            info = "numeric"
        elif col.dtype == "category":
            info = f"{col.unique_count} unique values"
        else:
            info = col.dtype
        if col.null_count > 0:
            info += f" ({col.null_count} nulls)"

        model_hint = col.suggested_model if col.suggested_model != DEFAULT_MODEL else ""
        table.add_row(str(col.index), col.name, col.dtype, info, model_hint)
    console.print(table)


def show_model_table(console: Console) -> None:
    table = Table(show_header=True, header_style="bold", pad_edge=False, show_lines=False)
    table.add_column("#", style="bold", width=4)
    table.add_column("Shortcut")
    table.add_column("Size")
    table.add_column("Description")
    table.add_column("Best For")
    models = list(MODEL_REGISTRY.values())
    domains = {
        "mini": "General text",
        "bge-large": "General text",
        "nomic": "Long documents",
        "gte": "General text",
        "e5": "General text",
        "address": "Addresses, locations",
        "entity": "Company names, entities",
    }
    for i, m in enumerate(models, 1):
        rec = " \u2605" if m.shortcut == DEFAULT_MODEL else ""
        domain = domains.get(m.shortcut, "")
        table.add_row(str(i), m.shortcut, f"~{m.size_mb} MB", f"{m.description}{rec}", domain)
    console.print(table)


def auto_detect_key(columns: list[ColumnInfo]) -> ColumnInfo | None:
    for col in columns:
        if col.is_likely_key:
            return col
    return None


def auto_detect_embed(columns: list[ColumnInfo]) -> list[int]:
    return [c.index for c in columns if c.is_likely_text or c.dtype in ("text", "category")]


def run_wizard(
    console: Console,
    quick: bool = False,
    file_override: Path | None = None,
    decimals: int = DEFAULT_DECIMALS,
) -> None:
    ensure_dirs()

    console.print(
        Panel(
            "[bold]Index Numerorum[/bold] -- Guided Mode\n"
            "[dim]Drop files into [cyan]input/[/cyan] and follow the prompts[/dim]",
            border_style="blue",
        )
    )

    file_path = file_override
    if file_path is None:
        file_path = _select_file(console, quick)
    if file_path is None:
        return

    df, columns = _load_and_inspect(console, file_path)
    key_col_name = _select_key(console, columns, df, quick)
    embed_indices = _select_embed(console, columns, quick)
    col_model_map = _select_models_per_column(console, columns, embed_indices, quick)
    top_k = _select_top_k(console, quick)

    embed_col_names = [columns[i - 1].name for i in embed_indices]
    model_summary = ", ".join(
        f"{name} ({resolve_model(m).id})" for name, m in col_model_map.items()
    )

    console.print(
        Panel(
            f"File:    [cyan]{file_path.name}[/cyan] ({len(df)} rows)\n"
            f"Key:     [cyan]{key_col_name}[/cyan]\n"
            f"Embed:   [cyan]{', '.join(embed_col_names)}[/cyan]\n"
            f"Models:  [cyan]{model_summary}[/cyan]\n"
            f"Top-K:   [cyan]{top_k}[/cyan]",
            title="Running",
            border_style="blue",
        )
    )

    phases: list[tuple[str, float]] = []
    df_work = df.copy()

    if key_col_name == AUTO_KEY_COLUMN:
        df_work[AUTO_KEY_COLUMN] = range(1, len(df_work) + 1)

    loaded_models: dict[str, object] = {}
    for _, model_shortcut in col_model_map.items():
        if model_shortcut not in loaded_models:
            model_info = resolve_model(model_shortcut)
            model_obj, t = spinner_phase(
                console, f"Loading model {model_info.id}", load_model, model_info
            )
            phases.append((f"Loaded {model_shortcut}", t))
            loaded_models[model_shortcut] = model_obj

    all_embeddings: list[np.ndarray] = []
    for col_name, model_shortcut in col_model_map.items():
        model_obj = loaded_models[model_shortcut]
        texts = df_work[col_name].fillna("").astype(str).tolist()

        start = time.time()
        embeddings = generate_embeddings(texts, model_obj, batch_size=DEFAULT_BATCH_SIZE)
        elapsed = time.time() - start
        console.print(
            f"[green]\u2713[/green] Embedded '{col_name}' with {model_shortcut} "
            f"({len(texts)} rows, {format_elapsed(elapsed)})"
        )
        phases.append((f"{col_name} embedded ({model_shortcut})", elapsed))
        all_embeddings.append(embeddings)

    combined = (
        np.mean(all_embeddings, axis=0).astype(np.float32)
        if len(all_embeddings) > 1
        else all_embeddings[0]
    )

    key_series = df_work[key_col_name].astype(str)
    keys = key_series.tolist()

    start = time.time()
    from .io import serialize_embedding

    emb_col = f"{EMBEDDING_COLUMN_PREFIX}_combined"
    df_work[emb_col] = [serialize_embedding(e) for e in combined]
    neighbors_df = find_neighbors(
        df_work, emb_col, metric=DEFAULT_METRIC, top_k=top_k, decimals=decimals
    )
    neighbors_df["query_key"] = [
        keys[i] if i < len(keys) else str(i) for i in range(len(neighbors_df))
    ]
    neighbor_keys = []
    for _, row in neighbors_df.iterrows():
        idx = row["rank"] - 1
        neighbor_keys.append(keys[idx] if idx < len(keys) else str(idx))
    elapsed = time.time() - start

    console.print(
        f"[green]\u2713[/green] Found {len(neighbors_df)} "
        f"neighbor pairs ({format_elapsed(elapsed)})"
    )
    phases.append((f"{len(neighbors_df)} neighbor pairs", elapsed))

    neighbors_df = neighbors_df[["query_key", "neighbor_key", "rank", "score"]]

    stem = file_path.stem
    nbor_path = OUTPUT_DIR / f"{stem}_neighbors.xlsx"

    _, t = spinner_phase(
        console, f"Writing {nbor_path.name}", write_xlsx, neighbors_df, nbor_path, None, True
    )
    phases.append((nbor_path.name, t))

    completion_panel(
        console,
        phases,
        output_path=f"output/{stem}_neighbors.xlsx",
        extra_stats={"Rows": str(len(df)), "Models used": str(len(loaded_models))},
    )


def _select_file(console: Console, quick: bool) -> Path | None:
    files = scan_input_files()
    if not files:
        console.print(
            Panel(
                "No .xlsx files found in [cyan]input/[/cyan]\n\n"
                "Drop your Excel files into the [cyan]input/[/cyan] folder and try again.",
                title="No Files",
                border_style="yellow",
            )
        )
        return None

    if quick and len(files) == 1:
        console.print(f"  Auto-selected: [cyan]{files[0].name}[/cyan]")
        return files[0]

    file_infos = []
    for f in files:
        rows, cols = read_file_info(f)
        file_infos.append((f.name, rows, cols))

    console.print(f"\n  Found {len(files)} file(s) in [cyan]input/[/cyan]:\n")
    show_file_table(console, file_infos)

    idx = prompt_choice(console, "Select a file", 1, len(files))
    return files[idx - 1]


def _load_and_inspect(console: Console, path: Path) -> tuple[pd.DataFrame, list[ColumnInfo]]:
    df = read_xlsx(path)
    columns = inspect_columns(df)
    console.print(f"\n  Columns in [cyan]{path.name}[/cyan] ({len(df)} rows):\n")
    show_columns(console, columns)
    console.print(
        "[dim]Model hints: address=addresses, entity=company names, mini=general text[/dim]"
    )
    return df, columns


def _select_key(console: Console, columns: list[ColumnInfo], df: pd.DataFrame, quick: bool) -> str:
    likely_key = auto_detect_key(columns)

    if quick and likely_key is not None:
        console.print(f"  Auto-detected key: [cyan]{likely_key.name}[/cyan]")
        return likely_key.name

    if likely_key is not None:
        console.print(f"\n  Likely key column: [cyan]{likely_key.index}. {likely_key.name}[/cyan]")

    console.print(f"  Press Enter with no input to auto-generate IDs ({AUTO_KEY_COLUMN})")
    raw = input(f"  Select KEY column [1-{len(columns)}] or press Enter: ").strip()

    if not raw:
        console.print(f"  Generated [cyan]{AUTO_KEY_COLUMN}[/cyan] (1 to {len(df)})")
        return AUTO_KEY_COLUMN

    try:
        idx = int(raw)
        if 1 <= idx <= len(columns):
            col = columns[idx - 1]
            if col.unique_count < col.total_count:
                console.print(
                    f"  [yellow]Warning: '{col.name}' has "
                    f"{col.unique_count} unique / {col.total_count} total rows.[/yellow]"
                )
            return col.name
    except ValueError:
        pass

    console.print("  [red]Invalid selection. Using first column.[/red]")
    return columns[0].name


def _select_embed(console: Console, columns: list[ColumnInfo], quick: bool) -> list[int]:
    text_indices = auto_detect_embed(columns)

    if quick and text_indices:
        names = [columns[i - 1].name for i in text_indices]
        console.print(f"  Auto-selected embed columns: [cyan]{', '.join(names)}[/cyan]")
        return text_indices

    return prompt_multi_choice(console, "Select column(s) to EMBED", len(columns))


def _select_models_per_column(
    console: Console,
    columns: list[ColumnInfo],
    embed_indices: list[int],
    quick: bool,
) -> dict[str, str]:
    col_model_map: dict[str, str] = {}
    shortcuts = list(MODEL_REGISTRY.keys())

    for idx in embed_indices:
        col = columns[idx - 1]
        suggested = col.suggested_model

        if quick:
            col_model_map[col.name] = suggested
            if suggested != DEFAULT_MODEL:
                console.print(f"  '{col.name}' -> auto-selected [cyan]{suggested}[/cyan] model")
            continue

        console.print(f"\n  Model for column [cyan]{col.name}[/cyan]:")
        show_model_table(console)
        default_idx = shortcuts.index(suggested) + 1 if suggested in shortcuts else 1
        raw = prompt_optional(console, f"  Select model for '{col.name}'", str(default_idx))
        try:
            choice = int(raw)
            if 1 <= choice <= len(shortcuts):
                col_model_map[col.name] = shortcuts[choice - 1]
                continue
        except ValueError:
            pass
        col_model_map[col.name] = suggested

    console.print("\n  Model assignments:")
    for col_name, model in col_model_map.items():
        tag = " (domain-specific)" if model != DEFAULT_MODEL else ""
        console.print(f"    [cyan]{col_name}[/cyan] -> [bold]{model}[/bold]{tag}")

    return col_model_map


def _select_top_k(console: Console, quick: bool) -> int:
    if quick:
        return DEFAULT_TOP_K
    raw = prompt_optional(console, "Top-K neighbors", str(DEFAULT_TOP_K))
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_TOP_K
