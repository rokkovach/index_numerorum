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
  wizard.py     # Interactive wizard: file scan, column inspect, multi-model embed, neighbors, post-run menu
  templates.py  # 5 business use case templates (sample xlsx + metadata + step-by-step guides)
  visuals.py    # Rich spinner helper and file table display
  config.py     # Model registry (7 models with best_for), column-model heuristics, constants, DEFAULT_DECIMALS
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
- **pytest** for tests

## Models

7 models in MODEL_REGISTRY, each with `best_for` field:
- `mini` (all-MiniLM-L6-v2) -- General text (default)
- `bge-large` (BAAI/bge-large-en-v1.5) -- General text, production
- `nomic` (nomic-ai/nomic-embed-text-v1.5) -- Long documents
- `gte` (Alibaba-NLP/gte-large-en-v1.5) -- General text
- `e5` (intfloat/e5-large-v2) -- General text
- `address` (pawan2411/address-emnet) -- Addresses, locations
- `entity` (themelder/arctic-embed-xs-entity-resolution) -- Company names, entities

Column-model heuristics in `suggest_model_for_column()` auto-assign `address` for columns containing "address", "street", "city", etc., and `entity` for "company", "vendor", "supplier", etc.

## Wizard Flow

Bare `index-numerorum` launches `run_wizard()` in wizard.py:
1. Scan `input/` for xlsx files (with spinner)
2. Read file and inspect columns (with spinner)
3. Prompt for key column (auto-generate if none)
4. Prompt for embed columns (auto-detect text columns)
5. Prompt for model per column (auto-suggest domain-specific models)
6. Load model(s) (with spinner), embed columns (with spinner)
7. Compute neighbors directly (with spinner)
8. Write results to `output/` (with spinner)
9. Post-run menu: run again, quick run, open output, quit

Multi-column embeddings are averaged into a combined vector. The wizard computes neighbors directly via `compute_pairwise` (not through `find_neighbors`) to avoid the `_emb_` prefix issue.

## zvec Notes

- zvec creates directories itself -- do NOT `mkdir()` before `create_and_open()` (causes ValueError)
- `collection.query()` takes `topk` as keyword arg, NOT on `VectorQuery()`
- Query returns `Doc` objects (`.id`, `.score`, `.fields`), not dicts
- COSINE metric score is cosine distance (0=identical); similarity = 1 - score
- zvec uses file locks -- cannot open same collection twice read-write
- Install via `pip install "index-numerorum[vec]"` (optional dependency)

## Security

- **Embedding columns stripped** from all xlsx output (cli.py embed command)
- **`np.load(allow_pickle=False)`** enforced in store.py
- **Atomic file writes** in store.py sidecar files (write-to-tmp + os.replace)
- **Formula injection sanitization** in io.py write_xlsx (prefixes `=`, `+`, `-`, `@`, `\t`, `\r` with `'`)
- **Sensitive values redacted** from error messages (neighbors.py)
- **HF telemetry disabled** via `HF_HUB_DISABLE_TELEMETRY=1` in embed.py
- **Symlink safety check** before rmtree in models --remove
- **GitHub Actions hardened**: SHA-pinned actions, `permissions: contents: read`, `persist-credentials: false`
- **.gitignore** covers `input/`, `output/`, `demo_output/`, `*.npy`, `*.npz`

## Commit Style

Short, imperative: "Add wizard mode with multi-model column detection"
