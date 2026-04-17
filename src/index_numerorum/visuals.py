from __future__ import annotations

import time
from collections.abc import Callable

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


def format_elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{seconds / 60:.1f}min"


def spinner(console: Console, message: str, func: Callable, *args, **kwargs):
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


def show_file_table(console: Console, files: list[tuple[str, int, int]]) -> None:
    table = Table(show_header=True, header_style="bold", pad_edge=False, show_lines=False)
    table.add_column("#", style="bold", width=4)
    table.add_column("File", style="cyan")
    table.add_column("Rows", justify="right")
    table.add_column("Cols", justify="right")
    for i, (name, rows, cols) in enumerate(files, 1):
        table.add_row(str(i), name, str(rows), str(cols))
    console.print(table)
