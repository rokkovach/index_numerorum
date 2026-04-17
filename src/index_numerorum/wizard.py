from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
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
from .io import read_xlsx, serialize_embedding, write_xlsx
from .neighbors import find_neighbors
from .visuals import format_elapsed

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


def _spinner(console: Console, message: str, func, *args, **kwargs):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(message, total=None)
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        progress.update(
            task,
            description=f"[green]\u2713[/green] {message} ({format_elapsed(elapsed)})",
        )
    return result, elapsed


def _prompt(console: Console, label: str, default: str = "") -> str:
    try:
        suffix = f" [{default}]" if default else ""
        raw = input(f"  {label}{suffix}: ").strip()
        return raw if raw else default
    except (EOFError, KeyboardInterrupt):
        console.print("\n  [yellow]Cancelled.[/yellow]")
        raise SystemExit(0) from None


def _prompt_int(console: Console, label: str, min_val: int, max_val: int) -> int:
    while True:
        try:
            raw = input(f"  {label} [{min_val}-{max_val}]: ").strip()
            if not raw:
                continue
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            console.print(f"  [red]Enter a number between {min_val} and {max_val}.[/red]")
        except ValueError:
            console.print(f"  [red]Enter a number between {min_val} and {max_val}.[/red]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [yellow]Cancelled.[/yellow]")
            raise SystemExit(0) from None


def _prompt_multi(console: Console, label: str, max_val: int) -> list[int]:
    while True:
        try:
            raw = input(f"  {label} [1-{max_val}, comma-separated]: ").strip()
            vals = [int(v.strip()) for v in raw.split(",") if v.strip()]
            if all(1 <= v <= max_val for v in vals) and vals:
                return vals
            console.print(f"  [red]Enter numbers between 1 and {max_val}.[/red]")
        except ValueError:
            console.print(f"  [red]Enter numbers between 1 and {max_val}.[/red]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n  [yellow]Cancelled.[/yellow]")
            raise SystemExit(0) from None


def _show_columns(console: Console, columns: list[ColumnInfo]) -> None:
    table = Table(show_header=True, header_style="bold", pad_edge=False, show_lines=False)
    table.add_column("#", style="bold", width=4)
    table.add_column("Column")
    table.add_column("Type", width=10)
    table.add_column("Info")
    table.add_column("Model", style="cyan", width=10)

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


def _show_models(console: Console) -> None:
    table = Table(show_header=True, header_style="bold", pad_edge=False, show_lines=False)
    table.add_column("#", style="bold", width=4)
    table.add_column("Shortcut")
    table.add_column("Size")
    table.add_column("Best For")
    domains = {
        "mini": "General text",
        "bge-large": "General text",
        "nomic": "Long documents",
        "gte": "General text",
        "e5": "General text",
        "address": "Addresses",
        "entity": "Company names",
    }
    for i, m in enumerate(MODEL_REGISTRY.values(), 1):
        rec = " \u2605" if m.shortcut == DEFAULT_MODEL else ""
        domain = domains.get(m.shortcut, "")
        table.add_row(str(i), m.shortcut, f"~{m.size_mb} MB", f"{domain}{rec}")
    console.print(table)


def _auto_key(columns: list[ColumnInfo]) -> ColumnInfo | None:
    for col in columns:
        if col.is_likely_key:
            return col
    return None


def _auto_embed(columns: list[ColumnInfo]) -> list[int]:
    return [c.index for c in columns if c.is_likely_text or c.dtype in ("text", "category")]


def _show_file_table(console: Console, files: list[tuple[str, int, int]]) -> None:
    table = Table(show_header=True, header_style="bold", pad_edge=False, show_lines=False)
    table.add_column("#", style="bold", width=4)
    table.add_column("File", style="cyan")
    table.add_column("Rows", justify="right")
    table.add_column("Cols", justify="right")
    for i, (name, rows, cols) in enumerate(files, 1):
        table.add_row(str(i), name, str(rows), str(cols))
    console.print(table)


def _read_file_info(path: Path) -> tuple[int, int]:
    try:
        full_df = pd.read_excel(path, engine="openpyxl")
        return len(full_df), len(full_df.columns)
    except Exception:
        return 0, 0


def run_wizard(
    console: Console,
    quick: bool = False,
    file_override: Path | None = None,
    decimals: int = DEFAULT_DECIMALS,
) -> None:
    ensure_dirs()

    console.print(
        Panel(
            "[bold]Index Numerorum[/bold] -- Local Embedding Toolkit\n"
            "[dim]Drop files into [cyan]input/[/cyan], get results in [cyan]output/[/cyan][/dim]",
            border_style="blue",
        )
    )

    while True:
        result_path = _run_pipeline(console, quick, file_override, decimals)
        if result_path is None:
            if not _post_run_menu(console, action="no_files"):
                break
            continue

        action = _post_run_menu(console, action="done", output_path=result_path)
        if action == "quit":
            break
        elif action == "rerun":
            continue
        elif action == "quick":
            quick = True
            continue


def _run_pipeline(
    console: Console, quick: bool, file_override: Path | None, decimals: int
) -> str | None:
    file_path = file_override
    if file_path is None:
        file_path = _pick_file(console, quick)
    if file_path is None:
        return None

    df, columns = _inspect_file(console, file_path)
    key_col = _pick_key(console, columns, df, quick)
    embed_indices = _pick_embed(console, columns, quick)
    col_model_map = _pick_models(console, columns, embed_indices, quick)
    top_k = _pick_top_k(console, quick)

    embed_col_names = [columns[i - 1].name for i in embed_indices]
    model_tags = ", ".join(
        f"{n}={m}" + (" \u2605" if m == DEFAULT_MODEL else "") for n, m in col_model_map.items()
    )

    console.print()
    console.print(
        Panel(
            f"File:    [cyan]{file_path.name}[/cyan] ({len(df)} rows)\n"
            f"Key:     [cyan]{key_col}[/cyan]\n"
            f"Embed:   [cyan]{', '.join(embed_col_names)}[/cyan]\n"
            f"Models:  [cyan]{model_tags}[/cyan]\n"
            f"Top-K:   [cyan]{top_k}[/cyan]",
            title="Running",
            border_style="blue",
        )
    )

    phases: list[tuple[str, float]] = []
    df_work = df.copy()
    if key_col == AUTO_KEY_COLUMN:
        df_work[AUTO_KEY_COLUMN] = range(1, len(df_work) + 1)

    loaded_models: dict[str, object] = {}
    for _, model_shortcut in col_model_map.items():
        if model_shortcut not in loaded_models:
            model_info = resolve_model(model_shortcut)
            model_obj, t = _spinner(
                console, f"Loading model {model_info.id}", load_model, model_info
            )
            phases.append((f"Loaded {model_shortcut}", t))
            loaded_models[model_shortcut] = model_obj

    all_embeddings: list[np.ndarray] = []
    for col_name, model_shortcut in col_model_map.items():
        model_obj = loaded_models[model_shortcut]
        texts = df_work[col_name].fillna("").astype(str).tolist()
        emb, t = _spinner(
            console,
            f"Embedding {col_name} ({len(texts)} rows, {model_shortcut})",
            generate_embeddings,
            texts,
            model_obj,
            DEFAULT_BATCH_SIZE,
        )
        phases.append((f"{col_name} ({model_shortcut})", t))
        all_embeddings.append(emb)

    combined = (
        np.mean(all_embeddings, axis=0).astype(np.float32)
        if len(all_embeddings) > 1
        else all_embeddings[0]
    )

    df_work[f"{EMBEDDING_COLUMN_PREFIX}_combined"] = [serialize_embedding(e) for e in combined]

    neighbors_df, t = _spinner(
        console,
        f"Finding neighbors ({len(df_work)} rows, top-{top_k})",
        find_neighbors,
        df_work,
        f"{EMBEDDING_COLUMN_PREFIX}_combined",
        DEFAULT_METRIC,
        top_k,
        decimals,
    )
    phases.append((f"{len(neighbors_df)} neighbor pairs", t))

    neighbors_df = neighbors_df[["query_key", "neighbor_key", "rank", "score"]]

    stem = file_path.stem
    nbor_path = OUTPUT_DIR / f"{stem}_neighbors.xlsx"
    _, t = _spinner(
        console, f"Writing {nbor_path.name}", write_xlsx, neighbors_df, nbor_path, None, True
    )
    phases.append((nbor_path.name, t))

    total_time = sum(t for _, t in phases)
    lines = []
    for label, t in phases:
        lines.append(f"  [green]\u2713[/green] {label} ({format_elapsed(t)})")
    lines.append(f"\n  [bold]Total: {format_elapsed(total_time)}[/bold]")
    lines.append(f"  Results: [cyan]{nbor_path}[/cyan]")
    console.print(Panel("\n".join(lines), title="Complete", border_style="green"))

    return str(nbor_path)


def _post_run_menu(console: Console, action: str, output_path: str | None = None) -> str:
    console.print()
    if action == "no_files":
        console.print(
            Panel(
                "No .xlsx files found in [cyan]input/[/cyan]\n\n"
                "Drop your Excel files into the [cyan]input/[/cyan] folder.",
                title="No Files",
                border_style="yellow",
            )
        )
        console.print("  [1] Retry (I added files)")
        console.print("  [q] Quit")
        raw = _prompt(console, "Choice", "q")
        return "quit" if raw.lower() in ("q", "quit", "") else "retry"

    console.print("  [1] Run again (different file)")
    console.print("  [2] Quick run (auto-detect everything)")
    console.print("  [3] Open output folder")
    console.print("  [q] Quit")
    raw = _prompt(console, "What next", "q")
    choice = raw.lower().strip()

    if choice in ("q", "quit", ""):
        console.print(Panel("Done. Results in [cyan]output/[/cyan]", border_style="blue"))
        return "quit"
    elif choice == "1":
        return "rerun"
    elif choice == "2":
        return "quick"
    elif choice == "3":
        import subprocess
        import sys

        folder = str(OUTPUT_DIR.resolve())
        try:
            if sys.platform == "darwin":
                subprocess.run(["open", folder], check=False)
            elif sys.platform == "win32":
                subprocess.run(["explorer", folder], check=False)
            else:
                subprocess.run(["xdg-open", folder], check=False)
        except Exception:
            console.print(f"  Output folder: [cyan]{folder}[/cyan]")
        return _post_run_menu(console, "done", output_path)
    return "quit"


def _pick_file(console: Console, quick: bool) -> Path | None:
    files, t_info = _spinner(console, "Scanning input/ for xlsx files", _scan_and_info)
    if not files:
        return None

    if quick and len(files) == 1:
        console.print(f"  Auto-selected: [cyan]{files[0][0].name}[/cyan] ({files[0][1]} rows)")
        return files[0][0]

    console.print(f"\n  Found {len(files)} file(s):\n")
    _show_file_table(console, [(f[0].name, f[1], f[2]) for f in files])
    idx = _prompt_int(console, "Select a file", 1, len(files))
    return files[idx - 1][0]


def _scan_and_info() -> list[tuple[Path, int, int]]:
    paths = scan_input_files()
    result = []
    for p in paths:
        rows, cols = _read_file_info(p)
        result.append((p, rows, cols))
    return result


def _inspect_file(console: Console, path: Path) -> tuple[pd.DataFrame, list[ColumnInfo]]:
    df, t = _spinner(console, f"Reading {path.name}", read_xlsx, path)
    columns = inspect_columns(df)
    console.print(f"\n  Columns in [cyan]{path.name}[/cyan] ({len(df)} rows):\n")
    _show_columns(console, columns)
    console.print("[dim]Hints: address=addresses, entity=company names, mini=general[/dim]")
    return df, columns


def _pick_key(console: Console, columns: list[ColumnInfo], df: pd.DataFrame, quick: bool) -> str:
    likely = _auto_key(columns)
    if quick and likely is not None:
        console.print(f"  Key: [cyan]{likely.name}[/cyan] (auto-detected)")
        return likely.name

    if likely is not None:
        console.print(f"\n  Likely key: [cyan]{likely.index}. {likely.name}[/cyan]")
    console.print(f"  Press Enter to auto-generate IDs ({AUTO_KEY_COLUMN})")
    raw = input(f"  Select KEY column [1-{len(columns)}] or Enter: ").strip()

    if not raw:
        console.print(f"  Generated [cyan]{AUTO_KEY_COLUMN}[/cyan] (1-{len(df)})")
        return AUTO_KEY_COLUMN

    try:
        idx = int(raw)
        if 1 <= idx <= len(columns):
            col = columns[idx - 1]
            if col.unique_count < col.total_count:
                console.print(
                    f"  [yellow]Warning: '{col.name}' has "
                    f"{col.unique_count} unique / {col.total_count} rows.[/yellow]"
                )
            return col.name
    except ValueError:
        pass
    console.print("  [red]Invalid. Using first column.[/red]")
    return columns[0].name


def _pick_embed(console: Console, columns: list[ColumnInfo], quick: bool) -> list[int]:
    text_indices = _auto_embed(columns)
    if quick and text_indices:
        names = [columns[i - 1].name for i in text_indices]
        console.print(f"  Embed: [cyan]{', '.join(names)}[/cyan] (auto-detected)")
        return text_indices
    return _prompt_multi(console, "Select column(s) to EMBED", len(columns))


def _pick_models(
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
                console.print(f"  {col.name} -> [cyan]{suggested}[/cyan] (auto)")
            continue

        console.print(f"\n  Model for [cyan]{col.name}[/cyan]:")
        _show_models(console)
        default_idx = shortcuts.index(suggested) + 1 if suggested in shortcuts else 1
        raw = _prompt(console, f"Model for '{col.name}'", str(default_idx))
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
        tag = " (domain)" if model != DEFAULT_MODEL else ""
        console.print(f"    [cyan]{col_name}[/cyan] -> [bold]{model}[/bold]{tag}")

    return col_model_map


def _pick_top_k(console: Console, quick: bool) -> int:
    if quick:
        return DEFAULT_TOP_K
    raw = _prompt(console, "Top-K neighbors", str(DEFAULT_TOP_K))
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_TOP_K
