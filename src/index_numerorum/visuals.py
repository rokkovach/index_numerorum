from __future__ import annotations

import time
from collections.abc import Callable

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.table import Table


def format_elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{seconds / 60:.1f}min"


def spinner_phase(console: Console, message: str, func: Callable, *args):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(message, total=None)
        start = time.time()
        result = func(*args)
        elapsed = time.time() - start
        progress.update(
            task, description=f"[green]\u2713[/green] {message} ({format_elapsed(elapsed)})"
        )
    return result, elapsed


def progress_phase(
    console: Console,
    message: str,
    total: int,
    func: Callable,
    *args,
) -> tuple:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("{task.completed}/{task.total}"),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(message, total=total)
        start = time.time()

        def update(completed: int) -> None:
            progress.update(task, completed=completed)

        result = func(*args, progress_callback=update)
        elapsed = time.time() - start
        progress.update(task, completed=total)
        console.print(f"[green]\u2713[/green] {message} ({format_elapsed(elapsed)})")
    return result, elapsed


def completion_panel(
    console: Console,
    phases: list[tuple[str, float]],
    output_path: str | None = None,
    extra_stats: dict[str, str] | None = None,
) -> None:
    total = sum(t for _, t in phases)
    lines = []
    for label, elapsed in phases:
        lines.append(f"  [green]\u2713[/green] {label} ({format_elapsed(elapsed)})")
    if extra_stats:
        for k, v in extra_stats.items():
            lines.append(f"  [green]\u2713[/green] {k}: {v}")
    if output_path:
        lines.append(f"\n  Results saved to [cyan]{output_path}[/cyan]")
    lines.append(f"\n  Total: {format_elapsed(total)}")
    console.print(Panel("\n".join(lines), title="Complete", border_style="green"))


def phase_tick(console: Console, message: str, elapsed: float) -> None:
    console.print(f"[green]\u2713[/green] {message} ({format_elapsed(elapsed)})")


def show_file_table(console: Console, files: list[tuple[str, int, int]]) -> None:
    table = Table(show_header=True, header_style="bold", pad_edge=False, show_lines=False)
    table.add_column("#", style="bold", width=4)
    table.add_column("File", style="cyan")
    table.add_column("Rows", justify="right")
    table.add_column("Columns", justify="right")
    for i, (name, rows, cols) in enumerate(files, 1):
        table.add_row(str(i), name, str(rows), str(cols))
    console.print(table)
