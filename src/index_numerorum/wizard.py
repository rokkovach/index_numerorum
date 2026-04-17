from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.table import Table

from .config import (
    DEFAULT_MODEL,
    DEFAULT_TOP_K,
    MODEL_REGISTRY,
    suggest_model_for_column,
)
from .io import read_xlsx
from .visuals import spinner

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
    for i, m in enumerate(MODEL_REGISTRY.values(), 1):
        rec = " \u2605" if m.shortcut == DEFAULT_MODEL else ""
        table.add_row(str(i), m.shortcut, f"~{m.size_mb} MB", f"{m.best_for}{rec}")
    console.print(table)


def _auto_key(columns: list[ColumnInfo]) -> ColumnInfo | None:
    for col in columns:
        if col.is_likely_key:
            return col
    return None


def _auto_embed(columns: list[ColumnInfo]) -> list[int]:
    return [c.index for c in columns if c.is_likely_text or c.dtype in ("text", "category")]


def _scan_and_info() -> list[tuple[Path, int, int]]:
    paths = scan_input_files()
    result = []
    for p in paths:
        try:
            full_df = pd.read_excel(p, engine="openpyxl")
            result.append((p, len(full_df), len(full_df.columns)))
        except Exception:
            result.append((p, 0, 0))
    return result


def _inspect_file(console: Console, path: Path) -> tuple[pd.DataFrame, list[ColumnInfo]]:
    df, t = spinner(console, f"Reading {path.name}", read_xlsx, path)
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
    raw = _prompt(console, f"Select KEY column [1-{len(columns)}] or Enter for auto-ID", "")

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
