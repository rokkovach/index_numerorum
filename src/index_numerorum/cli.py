from __future__ import annotations

import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

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


def _score_bar(score: float, metric: str, width: int = 20) -> str:
    if metric == "cosine":
        filled = int(max(0, min(width, (score + 1) / 2 * width)))
        return "[green]" + "\u2588" * filled + "[/green]" + "\u2591" * (width - filled)
    return ""


def _format_elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{seconds / 60:.1f}min"


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold]index-numerorum[/bold] {__version__}")
        raise typer.Exit()


def _handle_error(message: str, hint: str = "") -> None:
    content = f"[bold red]{message}[/bold red]"
    if hint:
        content += f"\n\n[hint]{hint}[/hint]"
    panel = Panel(content, title="Error", border_style="red")
    console.print(panel)
    raise typer.Exit(code=1)


EMBED_HELP = "Generate embeddings for text columns"
NEIGHBORS_HELP = "Find nearest neighbors for every row"
COMPARE_HELP = "Compare two specific records side-by-side"
COMPOSE_HELP = "Build a composite key from multiple columns"
MODELS_HELP = "List or download embedding models"
DEMO_HELP = "Run a guided demo with sample data"
DOCTOR_HELP = "Check your system environment"

EMBED_EPILOG = (
    "\n[bold]Examples:[/bold]\n\n"
    '[dim]# Single column[/dim]\n  index-numerorum embed data.xlsx -c "Product Name"\n\n'
    "[dim]# Multiple columns (each gets its own embedding)[/dim]\n"
    '  index-numerorum embed data.xlsx -c "Name" -c "Description"\n\n'
    "[dim]# Use a specific model[/dim]\n"
    '  index-numerorum embed data.xlsx -c "Name" -m bge-large\n'
)

NEIGHBORS_EPILOG = (
    "\n[bold]Examples:[/bold]\n\n"
    "[dim]# Find 10 most similar items[/dim]\n"
    '  index-numerorum neighbors embedded.xlsx -k "Product Name"\n\n'
    "[dim]# Custom metric and top-k[/dim]\n"
    '  index-numerorum neighbors embedded.xlsx -k "Name" --metric euclidean --top-k 5\n'
)

COMPARE_EPILOG = (
    "\n[bold]Examples:[/bold]\n\n"
    "[dim]# Compare two records[/dim]\n"
    '  index-numerorum compare embedded.xlsx -k "Name" -i "Widget A" -i "Widget B"\n'
)

COMPOSE_EPILOG = (
    "\n[bold]Examples:[/bold]\n\n"
    "[dim]# Concatenate first + last name[/dim]\n"
    '  index-numerorum compose-key staff.xlsx -c "First Name" -c "Last Name"\n\n'
    "[dim]# Weighted average with embedding[/dim]\n"
    '  index-numerorum compose-key data.xlsx -c "Title:0.7" -c "Abstract:0.3" '
    "-s weighted-average --embed\n"
)

MODELS_EPILOG = (
    "\n[bold]Examples:[/bold]\n\n"
    "[dim]# List all models[/dim]\n"
    "  index-numerorum models\n\n"
    "[dim]# Download a model for offline use[/dim]\n"
    "  index-numerorum models -d bge-large\n"
)

app = typer.Typer(
    name="index-numerorum",
    help="Index Numerorum -- local word embedding & similarity toolkit",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: bool | None = typer.Option(
        None, "--version", "-v", help="Show version", callback=_version_callback, is_eager=True
    ),
) -> None:
    pass


@app.command(help=EMBED_HELP, epilog=EMBED_EPILOG)
def embed(
    input: Path = typer.Argument(..., help="Input .xlsx file", exists=True),
    column: list[str] = typer.Option(..., "-c", "--column", help="Column(s) to embed"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model", help="Model shortcut or ID"),
    output: Path = typer.Option(None, "-o", "--output", help="Output file path"),
    batch_size: int = typer.Option(DEFAULT_BATCH_SIZE, "--batch-size", help="Batch size"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing embeddings"),
):
    try:
        df = read_xlsx(input)
        validate_columns(df, column)
    except (FileNotFoundError, ValueError) as e:
        _handle_error(str(e))
        return

    try:
        model_info = get_model_info(model)
    except ValueError as e:
        shortcuts = ", ".join(sorted(MODEL_REGISTRY))
        _handle_error(str(e), f"Shortcuts: {shortcuts}")
        return

    console.print(
        Panel(
            f"Model: [cyan]{model_info.id}[/cyan] "
            f"({model_info.dim} dims, {model_info.size_mb} MB)\n"
            f"Columns: [cyan]{', '.join(column)}[/cyan]\n"
            f"Rows: [cyan]{len(df)}[/cyan]",
            title="Embedding",
            border_style="blue",
        )
    )

    start = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Embedding rows...", total=None)
        sentence_model = load_model(model_info)
        df = embed_columns(df, column, sentence_model, batch_size=batch_size, force=force)
    elapsed = _format_elapsed(time.time() - start)

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

    console.print(
        Panel(
            f"[green]\u2713[/green] {len(column)} column(s) embedded ({model_info.dim} dims each)\n"
            f"[green]\u2713[/green] {len(df)} rows processed in {elapsed}\n"
            f"[bold]\u2192[/bold] {output_path}",
            title="Complete",
            border_style="green",
        )
    )


@app.command(help=NEIGHBORS_HELP, epilog=NEIGHBORS_EPILOG)
def neighbors(
    input: Path = typer.Argument(..., help="Input .xlsx file with embeddings", exists=True),
    key: str = typer.Option(..., "-k", "--key", help="Key column with embedded data"),
    metric: str = typer.Option(DEFAULT_METRIC, "--metric", help="Similarity metric"),
    top_k: int = typer.Option(DEFAULT_TOP_K, "--top-k", help="Number of neighbors"),
    threshold: float = typer.Option(
        None, "--threshold", "-t", help="Min similarity threshold (cosine only)"
    ),
    output: Path = typer.Option(None, "-o", "--output", help="Output file path"),
):
    valid_metrics = ["cosine", "euclidean", "manhattan", "dot"]
    if metric not in valid_metrics:
        _handle_error(
            f"Unknown metric '{metric}'.",
            f"Valid metrics: {', '.join(valid_metrics)}",
        )
        return

    try:
        df = read_xlsx(input)
    except (FileNotFoundError, ValueError) as e:
        _handle_error(str(e))
        return

    start = time.time()
    try:
        result_df = find_neighbors(df, key, metric=metric, top_k=top_k)
    except ValueError as e:
        msg = str(e)
        if "Embedding column" in msg:
            _handle_error(
                f"No embeddings found for column '{key}'.",
                f'Run [bold]embed[/bold] first:\n  index-numerorum embed {input.name} -c "{key}"',
            )
        else:
            _handle_error(msg)
        return
    elapsed = _format_elapsed(time.time() - start)

    if threshold is not None and metric == "cosine":
        before = len(result_df)
        result_df = result_df[result_df["score"] >= threshold].reset_index(drop=True)
        before - len(result_df)
    else:
        pass

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

    summary_line = (
        f"Key: [cyan]{key}[/cyan]    Metric: [cyan]{metric}[/cyan]    "
        f"Top-K: [cyan]{top_k}[/cyan]    Rows: [cyan]{len(df)}[/cyan]    "
        f"Pairs: [cyan]{len(result_df)}[/cyan]    {elapsed}"
    )
    console.print(Panel(summary_line, title="Neighbors", border_style="blue"))

    if len(result_df) > 0:
        first_query = result_df["query_key"].iloc[0]
        subset = result_df[result_df["query_key"] == first_query]

        preview = Table(
            title=f'Top neighbors for "{first_query}"',
            show_lines=False,
            title_style="bold",
            pad_edge=False,
        )
        preview.add_column("#", justify="right", style="bold", width=3)
        preview.add_column("Neighbor", min_width=20)
        preview.add_column("Score", justify="right", width=8)
        if metric == "cosine":
            preview.add_column("", width=20)

        for _, row in subset.head(top_k).iterrows():
            score = row["score"]
            neighbor = str(row["neighbor_key"])
            vals: list[str | Text] = [str(row["rank"]), neighbor, f"{score:.4f}"]
            if metric == "cosine":
                vals.append(_score_bar(score, metric))
            preview.add_row(*vals)
        console.print()
        console.print(preview)

    console.print(f"\n[bold green]\u2192[/bold green] {output_path}")


@app.command(help=COMPARE_HELP, epilog=COMPARE_EPILOG)
def compare(
    input: Path = typer.Argument(..., help="Input .xlsx file with embeddings", exists=True),
    key: str = typer.Option(..., "-k", "--key", help="Key column"),
    item: list[str] = typer.Option(
        ..., "-i", "--item", help="Two items to compare (exactly 2 required)"
    ),
    metric: str = typer.Option(DEFAULT_METRIC, "--metric", help="Metric to highlight"),
):
    if len(item) != 2:
        _handle_error(
            f"Expected exactly 2 items, got {len(item)}.",
            'Usage: -i "Item A" -i "Item B"',
        )
        return

    try:
        df = read_xlsx(input)
    except (FileNotFoundError, ValueError) as e:
        _handle_error(str(e))
        return

    start = time.time()
    try:
        scores = compare_items(df, key, item[0], item[1])
    except ValueError as e:
        msg = str(e)
        if "Embedding column" in msg:
            _handle_error(
                f"No embeddings found for column '{key}'.",
                f'Run [bold]embed[/bold] first:\n  index-numerorum embed {input.name} -c "{key}"',
            )
        elif "not found" in msg:
            _handle_error(msg)
        else:
            _handle_error(msg)
        return
    elapsed = _format_elapsed(time.time() - start)

    console.print(
        Panel(
            f'[cyan]"{item[0]}"[/cyan]  vs  [cyan]"{item[1]}"[/cyan]\n'
            f"Key: {key}    Highlighted: {metric}    {elapsed}",
            title="Comparison",
            border_style="blue",
        )
    )

    table = Table(show_lines=False, pad_edge=False)
    table.add_column("", width=2)
    table.add_column("Metric", style="bold")
    table.add_column("Score", justify="right", width=12)
    table.add_column("", width=20)

    for metric_name, score in scores.items():
        is_highlighted = metric_name == metric
        if is_highlighted:
            marker = "[green]\u25cf[/green]"
            name = f"[bold green]{metric_name}[/bold green]"
            score_str = f"[bold green]{score:.6f}[/bold green]"
            bar = _score_bar(score, metric_name)
        else:
            marker = " "
            name = f"[dim]{metric_name}[/dim]"
            score_str = f"[dim]{score:.6f}[/dim]"
            bar = ""
        table.add_row(marker, name, score_str, bar)

    console.print()
    console.print(table)


@app.command(name="compose-key", help=COMPOSE_HELP, epilog=COMPOSE_EPILOG)
def compose_key(
    input: Path = typer.Argument(..., help="Input .xlsx file", exists=True),
    columns: list[str] = typer.Option(..., "-c", "--column", help="Columns to compose"),
    strategy: str = typer.Option(
        "concatenate",
        "-s",
        "--strategy",
        help="Strategy: concatenate, average, weighted-average",
    ),
    separator: str = typer.Option(" ", "--separator", help="Separator for concatenate"),
    embed: bool = typer.Option(False, "--embed", help="Also embed the composite key"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model"),
    output: Path = typer.Option(None, "-o", "--output"),
    force: bool = typer.Option(False, "--force"),
):
    valid_strategies = ("concatenate", "average", "weighted-average")
    if strategy not in valid_strategies:
        _handle_error(
            f"Unknown strategy '{strategy}'.",
            f"Valid strategies: {', '.join(valid_strategies)}",
        )
        return

    try:
        df = read_xlsx(input)
        validate_columns(df, columns)
    except (FileNotFoundError, ValueError) as e:
        _handle_error(str(e))
        return

    composite = build_composite_key(df, columns, strategy=strategy, separator=separator)
    df[COMPOSITE_KEY_COLUMN] = composite

    sample = str(composite.iloc[0])
    if len(sample) > 50:
        sample = sample[:47] + "..."

    console.print(
        Panel(
            f"Columns: [cyan]{', '.join(columns)}[/cyan]\n"
            f"Strategy: [cyan]{strategy}[/cyan]\n"
            f"Sample: [dim]{sample}[/dim]",
            title="Composite Key",
            border_style="blue",
        )
    )

    model_id = "N/A"
    if embed:
        try:
            model_info = get_model_info(model)
            sentence_model = load_model(model_info)
            console.print(f"[dim]Embedding with {model_info.id} ({model_info.dim} dims)...[/dim]")
            df = embed_columns(df, [COMPOSITE_KEY_COLUMN], sentence_model, force=force)
            model_id = f"{model_info.id} ({model_info.dim} dims)"
        except ValueError as e:
            _handle_error(str(e))
            return

    output_path = output or input.with_name(f"{input.stem}_composed.xlsx")
    metadata = {
        "tool": "index-numerorum",
        "version": __version__,
        "command": "compose-key",
        "columns": ", ".join(columns),
        "strategy": strategy,
        "model": model_id,
        "date": datetime.now().isoformat(),
        "input_file": input.name,
        "input_rows": str(len(df)),
    }
    write_xlsx(df, output_path, metadata=metadata, overwrite=True)

    embed_info = f"\n[green]\u2713[/green] Embedded with {model_id}" if embed else ""
    console.print(
        Panel(
            f"[green]\u2713[/green] Key built from {len(columns)} column(s){embed_info}\n"
            f"[bold]\u2192[/bold] {output_path}",
            title="Complete",
            border_style="green",
        )
    )


@app.command(help=MODELS_HELP, epilog=MODELS_EPILOG)
def models(
    download: str = typer.Option(
        None, "--download", "-d", help="Download a model by shortcut or ID"
    ),
):
    if download is not None:
        try:
            model_info = resolve_model(download)
        except ValueError as e:
            _handle_error(str(e))
            return

        console.print(
            Panel(
                f"Downloading [bold]{model_info.id}[/bold] ({model_info.size_mb} MB)...",
                title="Download",
                border_style="blue",
            )
        )
        try:
            load_model(model_info)
        except Exception as e:
            _handle_error(f"Download failed: {e}")
            return
        console.print(
            Panel(
                f"[green]\u2713[/green] {model_info.id} cached locally",
                title="Complete",
                border_style="green",
            )
        )
        return

    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    table = Table(
        title="Available Models",
        show_lines=False,
        title_style="bold",
        pad_edge=False,
    )
    table.add_column("Shortcut", style="bold")
    table.add_column("Model ID")
    table.add_column("Dims", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Description")
    table.add_column("Cached", justify="center")

    for shortcut, info in MODEL_REGISTRY.items():
        model_folder_name = "models--" + info.id.replace("/", "--")
        cached = cache_dir.exists() and (cache_dir / model_folder_name).exists()
        cached_str = "[green]\u2713[/green]" if cached else "[dim]\u2717[/dim]"
        table.add_row(
            shortcut,
            info.id,
            str(info.dim),
            f"{info.size_mb} MB",
            info.description,
            cached_str,
        )

    console.print()
    console.print(table)
    console.print(
        "\n[dim]Use -m <shortcut> in any command. Or pass a full HuggingFace model ID.[/dim]"
    )


@app.command(help=DEMO_HELP)
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

    console.print(
        Panel(
            "Creating 20 sample products, embedding, and finding neighbors...",
            title="Index Numerorum Demo",
            border_style="blue",
        )
    )

    demo_dir = Path("demo_output")
    demo_dir.mkdir(exist_ok=True)

    sample_path = demo_dir / "products.xlsx"
    write_xlsx(df, sample_path, overwrite=True)

    model_info = get_model_info(DEFAULT_MODEL)
    start = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Loading model & embedding...", total=None)
        sentence_model = load_model(model_info)
        df_embedded = embed_columns(df.copy(), ["Name"], sentence_model)
        progress.update(task, description="Finding neighbors...")
        result_df = find_neighbors(df_embedded, "Name", metric="cosine", top_k=3)
    elapsed = _format_elapsed(time.time() - start)

    embedded_path = demo_dir / "products_embedded.xlsx"
    metadata = {
        "tool": "index-numerorum",
        "version": __version__,
        "command": "demo (embed)",
        "model": model_info.id,
        "date": datetime.now().isoformat(),
    }
    write_xlsx(df_embedded, embedded_path, metadata=metadata, overwrite=True)

    neighbors_path = demo_dir / "products_neighbors.xlsx"
    write_xlsx(result_df, neighbors_path, overwrite=True)

    console.print(
        Panel(
            f"\n  [green]\u2713[/green] products.xlsx             Source data (20 products)\n"
            f"  [green]\u2713[/green] products_embedded.xlsx    Data + embedding vectors\n"
            f"  [green]\u2713[/green] products_neighbors.xlsx   Nearest neighbor results\n\n"
            f"  [dim]Completed in {elapsed}[/dim]\n\n"
            f"  [dim]Open any file in Excel to explore. Try with your own data:[/dim]\n"
            f'  [cyan]index-numerorum embed your_file.xlsx -c "Column Name"[/cyan]\n',
            title="Demo Complete",
            border_style="green",
        )
    )


@app.command(help=DOCTOR_HELP)
def doctor():
    table = Table(
        title="Index Numerorum -- System Doctor",
        show_lines=False,
        title_style="bold",
        pad_edge=False,
    )
    table.add_column("Check", style="bold")
    table.add_column("Status")

    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    table.add_row(
        "Python version",
        f"[green]\u2713 {py_version}[/green]"
        if py_ok
        else f"[red]\u2717 {py_version} (need >= 3.11)[/red]",
    )

    try:
        import torch

        device = "cpu"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        table.add_row("PyTorch", f"[green]\u2713 {torch.__version__} ({device})[/green]")
    except ImportError:
        table.add_row("PyTorch", "[red]\u2717 not installed[/red]")

    try:
        import sentence_transformers

        table.add_row(
            "sentence-transformers",
            f"[green]\u2713 {sentence_transformers.__version__}[/green]",
        )
    except ImportError:
        table.add_row("sentence-transformers", "[red]\u2717 not installed[/red]")

    try:
        import zvec as _zvec

        table.add_row("zvec (optional)", f"[green]\u2713 {_zvec.__version__}[/green]")
    except ImportError:
        table.add_row(
            "zvec (optional)", "[dim]not installed (pip install index-numerorum[vec])[/dim]"
        )

    cache_dir = Path.home() / ".cache" / "huggingface"
    if cache_dir.exists():
        try:
            usage = shutil.disk_usage(cache_dir)
            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            table.add_row(
                "HF cache", f"[green]\u2713 {used_gb:.1f} GB used / {total_gb:.1f} GB total[/green]"
            )
        except OSError:
            table.add_row("HF cache", "[yellow]\u26a0 could not check[/yellow]")
    else:
        table.add_row("HF cache", "[dim]no cache directory yet[/dim]")

    console.print()
    console.print(table)
    console.print(
        f"\n[dim]index-numerorum v{__version__} | "
        f"Default model: {DEFAULT_MODEL} | Default metric: {DEFAULT_METRIC}[/dim]"
    )


@app.command(help="Manage persistent vector stores (requires zvec)")
def store(
    ctx: typer.Context,
) -> None:
    pass


store_app = typer.Typer(
    name="store",
    help="Persistent vector store operations (requires: pip install index-numerorum[vec])",
    rich_markup_mode="rich",
)
app.add_typer(store_app, name="store")


@store_app.command(name="init", help="Create a new vector store from an xlsx file")
def store_init(
    input: Path = typer.Argument(..., help="Input .xlsx file", exists=True),
    path: Path = typer.Argument(..., help="Store path (directory)"),
    key_column: str = typer.Option(..., "-k", "--key-column", help="Column with unique IDs"),
    embed_column: list[str] = typer.Option(..., "-c", "--embed-column", help="Column(s) to embed"),
    model: str = typer.Option(DEFAULT_MODEL, "-m", "--model"),
    batch_size: int = typer.Option(DEFAULT_BATCH_SIZE, "--batch-size"),
) -> None:
    try:
        from .store import VectorStore
    except ImportError as e:
        _handle_error(str(e))
        return

    try:
        df = read_xlsx(input)
        validate_columns(df, [key_column, *list(embed_column)])
        model_info = resolve_model(model)
    except (FileNotFoundError, ValueError) as e:
        _handle_error(str(e))
        return

    console.print(
        Panel(
            f"Input: [cyan]{input.name}[/cyan] ({len(df)} rows)\n"
            f"Model: [cyan]{model_info.id}[/cyan] ({model_info.dim} dims)\n"
            f"Key: [cyan]{key_column}[/cyan]    Embed: [cyan]{', '.join(embed_column)}[/cyan]",
            title="Creating Store",
            border_style="blue",
        )
    )

    start = time.time()
    from .embed import load_model

    sentence_model = load_model(model_info)
    texts = df[embed_column[0]].fillna("").astype(str)
    for col in embed_column[1:]:
        texts = texts + " " + df[col].fillna("").astype(str)

    embeddings = sentence_model.encode(
        texts.tolist(), batch_size=batch_size, show_progress_bar=False
    )
    embeddings = np.array(embeddings, dtype=np.float32)

    store_obj = VectorStore.create(
        path=path,
        model_id=model_info.id,
        dimensions=model_info.dim,
        key_column=key_column,
        embed_columns=list(embed_column),
    )
    key_values = df[key_column].astype(str).tolist()
    store_obj.insert_rows(df, embeddings, key_values)
    elapsed = _format_elapsed(time.time() - start)

    console.print(
        Panel(
            f"[green]\u2713[/green] Store created at {path}\n"
            f"[green]\u2713[/green] {len(df)} rows embedded and stored\n"
            f"  Model: {model_info.id} ({model_info.dim} dims)\n"
            f"  Key: {key_column}    Embed: {', '.join(embed_column)}\n"
            f"  {elapsed}",
            title="Store Created",
            border_style="green",
        )
    )


@store_app.command(name="add", help="Add rows from xlsx to an existing store")
def store_add(
    path: Path = typer.Argument(..., help="Store path"),
    input: Path = typer.Argument(..., help="Input .xlsx file", exists=True),
    batch_size: int = typer.Option(DEFAULT_BATCH_SIZE, "--batch-size"),
) -> None:
    try:
        from .store import VectorStore
    except ImportError as e:
        _handle_error(str(e))
        return

    try:
        store_obj = VectorStore(path)
        df = read_xlsx(input)
        key_col = store_obj.key_column
        validate_columns(df, [key_col, *store_obj.embed_columns])
    except Exception as e:
        _handle_error(str(e))
        return

    existing_keys = set(store_obj._keys)
    key_values = df[key_col].astype(str).tolist()
    mask = [k not in existing_keys for k in key_values]
    new_df = df[mask].reset_index(drop=True)
    new_keys = [k for k, m in zip(key_values, mask, strict=False) if m]
    skipped = len(df) - len(new_df)

    if len(new_df) == 0:
        console.print(
            Panel(
                f"All {len(df)} rows already in store. Nothing to add.",
                title="Store Add",
                border_style="yellow",
            )
        )
        return

    from .embed import load_model

    model_info = resolve_model(store_obj.model_id)
    sentence_model = load_model(model_info)

    texts = new_df[store_obj.embed_columns[0]].fillna("").astype(str)
    for col in store_obj.embed_columns[1:]:
        texts = texts + " " + new_df[col].fillna("").astype(str)

    start = time.time()
    embeddings = sentence_model.encode(
        texts.tolist(), batch_size=batch_size, show_progress_bar=False
    )
    embeddings = np.array(embeddings, dtype=np.float32)
    store_obj.insert_rows(new_df, embeddings, new_keys)
    elapsed = _format_elapsed(time.time() - start)

    console.print(
        Panel(
            f"[green]\u2713[/green] {len(new_df)} rows added\n"
            f"  {skipped} rows skipped (already in store)\n"
            f"  Store now has {store_obj.row_count} rows\n"
            f"  {elapsed}",
            title="Store Updated",
            border_style="green",
        )
    )


@store_app.command(name="match", help="Find all pairs above similarity threshold")
def store_match(
    path: Path = typer.Argument(..., help="Store path"),
    threshold: float = typer.Option(0.90, "-t", "--threshold", help="Similarity threshold (0-1)"),
    output: Path = typer.Option(None, "-o", "--output", help="Output xlsx path"),
) -> None:
    try:
        from .store import VectorStore
    except ImportError as e:
        _handle_error(str(e))
        return

    try:
        store_obj = VectorStore(path)
    except Exception as e:
        _handle_error(str(e))
        return

    console.print(
        Panel(
            f"Store: [cyan]{path}[/cyan] ({store_obj.row_count} rows)\n"
            f"Threshold: [cyan]{threshold}[/cyan]",
            title="Matching",
            border_style="blue",
        )
    )

    start = time.time()
    result_df = store_obj.match_all(threshold)
    elapsed = _format_elapsed(time.time() - start)

    if result_df.empty:
        console.print(
            Panel(
                f"No matches found above {threshold}.\n"
                f"Try lowering --threshold (e.g., 0.80).\n"
                f"  {elapsed}",
                title="No Matches",
                border_style="yellow",
            )
        )
        return

    n_groups = result_df["group_id"].nunique()
    output_path = output or Path(f"matches_{path.name}.xlsx")
    metadata = {
        "tool": "index-numerorum",
        "version": __version__,
        "command": "store match",
        "threshold": str(threshold),
        "total_pairs": str(len(result_df)),
        "dedup_groups": str(n_groups),
        "date": datetime.now().isoformat(),
    }
    write_xlsx(result_df, output_path, metadata=metadata, overwrite=True)

    console.print(
        Panel(
            f"[green]\u2713[/green] {len(result_df)} matching pairs found\n"
            f"  {n_groups} dedup groups\n"
            f"  Threshold: {threshold}\n"
            f"  {elapsed}\n"
            f"[bold]\u2192[/bold] {output_path}",
            title="Match Complete",
            border_style="green",
        )
    )


@store_app.command(name="annotate", help="Write match annotations back into xlsx")
def store_annotate(
    path: Path = typer.Argument(..., help="Store path"),
    input: Path = typer.Argument(..., help="Input .xlsx file to annotate", exists=True),
    threshold: float = typer.Option(0.90, "-t", "--threshold", help="Similarity threshold"),
    output: Path = typer.Option(None, "-o", "--output", help="Output xlsx path"),
) -> None:
    try:
        from .store import VectorStore
    except ImportError as e:
        _handle_error(str(e))
        return

    try:
        store_obj = VectorStore(path)
        df = read_xlsx(input)
    except Exception as e:
        _handle_error(str(e))
        return

    start = time.time()
    result_df = store_annotate_df(store_obj, df, threshold)
    elapsed = _format_elapsed(time.time() - start)

    output_path = output or input.with_name(f"{input.stem}_annotated.xlsx")
    write_xlsx(result_df, output_path, overwrite=True)

    match_count = (result_df["_match_count"] > 0).sum()
    n_groups = result_df["_group_id"].nunique() - (1 if 0 in result_df["_group_id"].values else 0)
    console.print(
        Panel(
            f"[green]\u2713[/green] {match_count} rows have matches "
            f"({n_groups} dedup groups)\n"
            f"  Threshold: {threshold}    {elapsed}\n"
            f"  Added: _match_count, _match_ids, "
            f"_best_match_id, _best_match_score, _group_id\n"
            f"[bold]\u2192[/bold] {output_path}",
            title="Annotation Complete",
            border_style="green",
        )
    )


def store_annotate_df(store_obj: object, df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    result = store_obj.annotate(df, threshold)
    result["_match_ids"] = result["_match_ids"].apply(
        lambda x: ", ".join(x) if isinstance(x, list) else str(x)
    )
    return result


@store_app.command(name="query", help="Query store with free text")
def store_query_cmd(
    path: Path = typer.Argument(..., help="Store path"),
    text: str = typer.Option(..., "-t", "--text", help="Search text"),
    top_k: int = typer.Option(10, "--top-k", help="Number of results"),
) -> None:
    try:
        from .store import VectorStore
    except ImportError as e:
        _handle_error(str(e))
        return

    try:
        store_obj = VectorStore(path)
    except Exception as e:
        _handle_error(str(e))
        return

    from .embed import load_model

    model_info = resolve_model(store_obj.model_id)
    sentence_model = load_model(model_info)

    start = time.time()
    results = store_obj.query_by_text(text, sentence_model, top_k=top_k)
    elapsed = _format_elapsed(time.time() - start)

    if not results:
        console.print("[dim]No results found.[/dim]")
        return

    console.print(
        Panel(
            f'Query: [cyan]"{text}"[/cyan]\nStore: {store_obj.row_count} rows    {elapsed}',
            title="Query",
            border_style="blue",
        )
    )

    table = Table(show_lines=False, pad_edge=False)
    table.add_column("#", justify="right", style="bold", width=3)
    table.add_column("ID")
    table.add_column("Score", justify="right", width=8)
    table.add_column("", width=20)

    for i, r in enumerate(results, 1):
        score = r["similarity"]
        bar = _score_bar(score, "cosine")
        table.add_row(str(i), str(r["id"]), f"{score:.4f}", bar)

    console.print()
    console.print(table)


@store_app.command(name="info", help="Show store metadata")
def store_info(
    path: Path = typer.Argument(..., help="Store path"),
) -> None:
    try:
        from .store import VectorStore
    except ImportError as e:
        _handle_error(str(e))
        return

    try:
        store_obj = VectorStore(path)
    except Exception as e:
        _handle_error(str(e))
        return

    info = store_obj.info()
    size_mb = info["size_on_disk"] / (1024 * 1024)

    console.print(
        Panel(
            f"Path: [cyan]{info['path']}[/cyan]\n"
            f"Rows: [cyan]{info['row_count']}[/cyan]\n"
            f"Model: [cyan]{info['model_id']}[/cyan] ({info['dimensions']} dims)\n"
            f"Key column: [cyan]{info['key_column']}[/cyan]\n"
            f"Embed columns: [cyan]{', '.join(info['embed_columns'])}[/cyan]\n"
            f"Size on disk: [cyan]{size_mb:.1f} MB[/cyan]",
            title="Store Info",
            border_style="blue",
        )
    )


if __name__ == "__main__":
    app()
