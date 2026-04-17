from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .config import (
    COMPOSITE_KEY_COLUMN,
    DEFAULT_BATCH_SIZE,
    DEFAULT_METRIC,
    DEFAULT_MODEL,
    DEFAULT_TOP_K,
    MODEL_REGISTRY,
    resolve_model,
)
from .embed import embed_columns, get_model_info, load_model
from .io import read_xlsx, validate_columns, write_xlsx
from .keys import build_composite_key
from .neighbors import compare_items, find_neighbors

console = Console()
app = typer.Typer(
    name="index-numerorum",
    help="Index Numerorum — local word embedding & similarity toolkit",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.command()
def embed(
    input: Path = typer.Argument(..., help="Input .xlsx file", exists=True),
    column: list[str] = typer.Option(..., "-c", "--column", help="Column(s) to embed"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model", help="Model shortcut or ID"),
    output: Path = typer.Option(None, "-o", "--output", help="Output file path"),
    batch_size: int = typer.Option(DEFAULT_BATCH_SIZE, "--batch-size", help="Batch size"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing embeddings"),
):
    df = read_xlsx(input)
    validate_columns(df, column)

    model_info = get_model_info(model)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading model...", total=None)
        sentence_model = load_model(model_info)
        progress.update(task, description="Generating embeddings...")
        df = embed_columns(df, column, sentence_model, batch_size=batch_size, force=force)
        progress.update(task, description="Done.")

    output_path = output or input.with_name(f"{input.stem}_embedded.xlsx")
    metadata = {
        "tool": "index-numerorum",
        "version": __version__,
        "command": "embed",
        "model": model_info.id,
        "model_dim": str(model_info.dim),
        "date": datetime.now().isoformat(),
        "input_file": input.name,
        "input_rows": str(len(df)),
    }
    write_xlsx(df, output_path, metadata=metadata, overwrite=True)

    console.print(f"[bold green]Success![/bold green] Written to {output_path}")


@app.command()
def neighbors(
    input: Path = typer.Argument(..., help="Input .xlsx file with embeddings", exists=True),
    key: str = typer.Option(..., "-k", "--key", help="Key column with embedded data"),
    metric: str = typer.Option(DEFAULT_METRIC, "--metric", help="Similarity metric"),
    top_k: int = typer.Option(DEFAULT_TOP_K, "--top-k", help="Number of neighbors"),
    output: Path = typer.Option(None, "-o", "--output", help="Output file path"),
):
    df = read_xlsx(input)
    result_df = find_neighbors(df, key, metric=metric, top_k=top_k)

    output_path = output or input.with_name(f"{input.stem}_neighbors.xlsx")
    metadata = {
        "tool": "index-numerorum",
        "version": __version__,
        "command": "neighbors",
        "key_column": key,
        "metric": metric,
        "top_k": str(top_k),
        "date": datetime.now().isoformat(),
        "input_file": input.name,
        "input_rows": str(len(df)),
    }
    write_xlsx(result_df, output_path, metadata=metadata, overwrite=True)

    summary = Panel(
        f"[bold]Neighbors computed[/bold]\n"
        f"Key: {key}  |  Metric: {metric}  |  Top-K: {top_k}\n"
        f"Total pairs: {len(result_df)}",
        title="Neighbors Summary",
    )
    console.print(summary)

    preview_table = Table(title="Preview (first query)")
    preview_table.add_column("Rank", justify="right")
    preview_table.add_column("Neighbor")
    preview_table.add_column("Score", justify="right")
    first_query = result_df[result_df["query_key"] == result_df["query_key"].iloc[0]]
    for _, row in first_query.head(5).iterrows():
        preview_table.add_row(str(row["rank"]), str(row["neighbor_key"]), f"{row['score']:.4f}")
    console.print(preview_table)

    console.print(f"\n[bold green]Written to {output_path}[/bold green]")


@app.command()
def compare(
    input: Path = typer.Argument(..., help="Input .xlsx file with embeddings", exists=True),
    key: str = typer.Option(..., "-k", "--key", help="Key column"),
    item: list[str] = typer.Option(..., "-i", "--item", help="Two items to compare (exactly 2)"),
    metric: str = typer.Option(DEFAULT_METRIC, "--metric", help="Metric to display"),
):
    if len(item) != 2:
        console.print("[bold red]Error:[/bold red] Exactly 2 items required for comparison.")
        raise typer.Exit(code=1)

    df = read_xlsx(input)
    scores = compare_items(df, key, item[0], item[1])

    table = Table(title=f"Comparison: {item[0]} vs {item[1]}")
    table.add_column("Metric")
    table.add_column("Score", justify="right")
    for metric_name, score in scores.items():
        highlight = "[bold green]" if metric_name == metric else ""
        reset = "[/bold green]" if metric_name == metric else ""
        table.add_row(metric_name, f"{highlight}{score:.6f}{reset}")
    console.print(table)


@app.command(name="compose-key")
def compose_key(
    input: Path = typer.Argument(..., help="Input .xlsx file", exists=True),
    columns: list[str] = typer.Option(..., "-c", "--column", help="Columns to compose"),
    strategy: str = typer.Option(
        "concatenate", "-s", "--strategy", help="Strategy: concatenate, average, weighted-average"
    ),
    separator: str = typer.Option(" ", "--separator", help="Separator for concatenate"),
    embed: bool = typer.Option(False, "--embed", help="Also embed the composite key"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model"),
    output: Path = typer.Option(None, "-o", "--output"),
    force: bool = typer.Option(False, "--force"),
):
    valid_strategies = ("concatenate", "average", "weighted-average")
    if strategy not in valid_strategies:
        console.print(
            f"[bold red]Error:[/bold red] Unknown strategy "
            f"'{strategy}'. Valid: {list(valid_strategies)}"
        )
        raise typer.Exit(code=1)

    df = read_xlsx(input)
    validate_columns(df, columns)

    composite = build_composite_key(df, columns, strategy=strategy, separator=separator)
    df[COMPOSITE_KEY_COLUMN] = composite

    if embed:
        model_info = get_model_info(model)
        sentence_model = load_model(model_info)
        df = embed_columns(df, [COMPOSITE_KEY_COLUMN], sentence_model, force=force)

    output_path = output or input.with_name(f"{input.stem}_composed.xlsx")
    metadata = {
        "tool": "index-numerorum",
        "version": __version__,
        "command": "compose-key",
        "columns": ", ".join(columns),
        "strategy": strategy,
        "model": model if embed else "N/A",
        "date": datetime.now().isoformat(),
        "input_file": input.name,
        "input_rows": str(len(df)),
    }
    write_xlsx(df, output_path, metadata=metadata, overwrite=True)
    console.print(f"[bold green]Success![/bold green] Written to {output_path}")


@app.command()
def models(
    download: str = typer.Option(
        None, "--download", "-d", help="Download a model by shortcut or ID"
    ),
):
    if download is not None:
        model_info = resolve_model(download)
        console.print(f"Downloading [bold]{model_info.id}[/bold]...")
        load_model(model_info)
        console.print("[bold green]Download complete.[/bold green]")
        return

    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    table = Table(title="Available Models")
    table.add_column("Shortcut", style="bold")
    table.add_column("Model ID")
    table.add_column("Dimensions", justify="right")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Description")
    table.add_column("Cached", justify="center")

    for shortcut, info in MODEL_REGISTRY.items():
        model_folder_name = "models--" + info.id.replace("/", "--")
        cached = cache_dir.exists() and (cache_dir / model_folder_name).exists()
        cached_str = "[green]✓[/green]" if cached else "[red]✗[/red]"
        table.add_row(
            shortcut,
            info.id,
            str(info.dim),
            str(info.size_mb),
            info.description,
            cached_str,
        )

    console.print(table)


@app.command()
def demo():
    products = [
        {"ID": i, "Name": name, "Category": cat, "Description": desc}
        for i, (name, cat, desc) in enumerate(
            [
                ("Wireless Mouse", "Electronics", "Bluetooth mouse with ergonomic design"),
                ("USB-C Hub", "Electronics", "7-in-1 USB hub with HDMI and ethernet"),
                ("Mechanical Keyboard", "Electronics", "RGB cherry MX blue switch keyboard"),
                (
                    "Noise Cancelling Headphones",
                    "Electronics",
                    "Over-ear ANC headphones with 30h battery",
                ),
                ("Portable Charger", "Electronics", "20000mAh power bank with fast charging"),
                ("Standing Desk Mat", "Office", "Anti-fatigue cushioned floor mat"),
                ("Desk Organizer", "Office", "Bamboo desktop organizer with drawers"),
                ("Ergonomic Chair", "Office", "Lumbar support mesh office chair"),
                ("Monitor Arm", "Office", "Gas spring single monitor mount"),
                ("Whiteboard", "Office", "Magnetic dry-erase whiteboard 48x36"),
                ("Chef Knife Set", "Kitchen", "Japanese steel 6-piece knife block set"),
                ("Air Fryer", "Kitchen", "Digital 5.8qt air fryer with presets"),
                ("French Press", "Kitchen", "Borosilicate glass 34oz coffee press"),
                ("Cast Iron Skillet", "Kitchen", "Pre-seasoned 12-inch cast iron pan"),
                ("Blender", "Kitchen", "High-speed 1400W professional blender"),
                ("Yoga Mat", "Sports", "Extra thick non-slip exercise mat"),
                ("Resistance Bands", "Sports", "Set of 5 latex loop bands"),
                ("Jump Rope", "Sports", "Adjustable speed jump rope with bearings"),
                ("Foam Roller", "Sports", "High-density textured muscle roller"),
                ("Water Bottle", "Sports", "Insulated stainless steel 32oz bottle"),
            ],
            1,
        )
    ]

    df = pd.DataFrame(products)

    demo_dir = Path("demo_output")
    demo_dir.mkdir(exist_ok=True)

    sample_path = demo_dir / "products.xlsx"
    write_xlsx(df, sample_path, overwrite=True)
    console.print(f"Sample data written to {sample_path}")

    model_info = get_model_info(DEFAULT_MODEL)
    sentence_model = load_model(model_info)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Embedding Name column...", total=None)
        df_embedded = embed_columns(df.copy(), ["Name"], sentence_model)
        progress.update(task, description="Done.")

    embedded_path = demo_dir / "products_embedded.xlsx"
    metadata = {
        "tool": "index-numerorum",
        "version": __version__,
        "command": "demo (embed)",
        "model": model_info.id,
        "date": datetime.now().isoformat(),
    }
    write_xlsx(df_embedded, embedded_path, metadata=metadata, overwrite=True)
    console.print(f"Embedded data written to {embedded_path}")

    result_df = find_neighbors(df_embedded, "Name", metric="cosine", top_k=3)
    neighbors_path = demo_dir / "products_neighbors.xlsx"
    write_xlsx(result_df, neighbors_path, overwrite=True)
    console.print(f"Neighbors written to {neighbors_path}")

    console.print(
        Panel(
            f"[bold green]Demo complete![/bold green]\n\n"
            f"Files in [cyan]{demo_dir}/[/cyan]:\n"
            f"  • products.xlsx\n"
            f"  • products_embedded.xlsx\n"
            f"  • products_neighbors.xlsx",
            title="Demo Results",
        )
    )


@app.command()
def doctor():
    table = Table(title="Index Numerorum — System Doctor")
    table.add_column("Check")
    table.add_column("Status")

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    table.add_row(
        "Python version",
        f"[green]✓ {py_version}[/green]" if py_ok else f"[red]✗ {py_version} (need >= 3.10)[/red]",
    )

    try:
        import torch

        table.add_row("PyTorch", f"[green]✓ {torch.__version__}[/green]")
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            table.add_row("MPS (Apple Silicon)", "[green]✓ available[/green]")
        else:
            table.add_row("MPS (Apple Silicon)", "[dim]not available[/dim]")
    except ImportError:
        table.add_row("PyTorch", "[red]✗ not installed[/red]")

    try:
        import sentence_transformers

        table.add_row(
            "sentence-transformers", f"[green]✓ {sentence_transformers.__version__}[/green]"
        )
    except ImportError:
        table.add_row("sentence-transformers", "[red]✗ not installed[/red]")

    cache_dir = Path.home() / ".cache" / "huggingface"
    if cache_dir.exists():
        try:
            usage = shutil.disk_usage(cache_dir)
            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            table.add_row(
                "HF cache disk", f"[green]✓ {used_gb:.1f} GB used / {total_gb:.1f} GB total[/green]"
            )
        except OSError:
            table.add_row("HF cache disk", "[yellow]⚠ could not check[/yellow]")
    else:
        table.add_row("HF cache disk", "[dim]no cache directory yet[/dim]")

    console.print(table)


if __name__ == "__main__":
    app()
