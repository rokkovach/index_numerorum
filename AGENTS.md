# AGENTS.md

Instructions for AI agents working on this project.

## Project Overview

Index Numerorum is a Python CLI tool for generating local word embeddings from Excel files, finding nearest neighbors, and matching records. All processing is local (zero data egress) using sentence-transformers.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install -e ".[vec]"  # optional: zvec vector store
```

## Commands

### Lint
```bash
ruff check src/ tests/
ruff format --check src/ tests/
```

Fix automatically:
```bash
ruff check --fix src/ tests/
ruff format src/ tests/
```

### Tests
```bash
pytest tests/ -v
```

Run only unit tests (fast, no model downloads):
```bash
pytest tests/unit/ -v
```

Integration tests require downloading models (~80 MB first run):
```bash
pytest tests/integration/ -v
```

## Architecture

```
src/index_numerorum/
  cli.py        # Typer CLI app. Bare invocation launches wizard (wizard.py)
  wizard.py     # Interactive wizard: file scan, column inspect, multi-model embed, neighbors
  visuals.py    # Rich progress helpers: spinners, progress bars, completion panels
  config.py     # Model registry (7 models), column-model heuristics, constants
  embed.py      # load_model (with logging suppression), generate_embeddings, embed_columns
  io.py         # XLSX read/write, validate_columns, embedding serialization
  keys.py       # Composite key construction (concatenate, average, weighted-average)
  neighbors.py  # find_neighbors, compare_items (with configurable decimal rounding)
  similarity.py # cosine, euclidean, manhattan, dot + pairwise versions
  store.py      # VectorStore class (zvec-backed), union-find grouping
```

## Key Conventions

- **Python 3.11+**, type hints everywhere
- **Rich** for all terminal output (panels, tables, progress bars, error panels)
- **Never show raw tracebacks** to users -- wrap all errors in Rich error panels
- **Never save embeddings in xlsx** -- embeddings are internal only, output only neighbor results
- **Scores rounded to 2 decimals** by default (`DEFAULT_DECIMALS` in config.py), configurable via `--decimals`
- **No comments in code** unless explicitly requested
- **Ruff** for lint + format, target Python 3.11, line length 100
- **pytest** for tests, 124 tests currently passing

## Models

7 models in MODEL_REGISTRY:
- `mini` (all-MiniLM-L6-v2) -- default, general text
- `bge-large` (BAAI/bge-large-en-v1.5) -- top accuracy
- `nomic` (nomic-ai/nomic-embed-text-v1.5) -- long context
- `gte` (Alibaba-NLP/gte-large-en-v1.5) -- cutting-edge
- `e5` (intfloat/e5-large-v2) -- well-tested
- `address` (pawan2411/address-emnet) -- address matching & dedup
- `entity` (themelder/arctic-embed-xs-entity-resolution) -- company names, entity resolution

Column-model heuristics in `suggest_model_for_column()` auto-assign `address` for columns containing "address", "street", "city", etc., and `entity` for "company", "vendor", "supplier", etc.

## zvec Notes

- zvec creates directories itself -- do NOT `mkdir()` before `create_and_open()` (causes ValueError)
- `collection.query()` takes `topk` as keyword arg, NOT on `VectorQuery()`
- Query returns `Doc` objects (`.id`, `.score`, `.fields`), not dicts
- COSINE metric score is cosine distance (0=identical); similarity = 1 - score
- zvec uses file locks -- cannot open same collection twice read-write
- Install via `pip install "index-numerorum[vec]"` (optional dependency)

## Commit Style

Short, imperative: "Add wizard mode with multi-model column detection"
