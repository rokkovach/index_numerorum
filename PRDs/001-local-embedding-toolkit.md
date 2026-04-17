# PRD: Index Numerorum

## Local Word Embedding & Similarity Toolkit

**Version:** 1.0  
**Date:** 2026-04-17  
**Author:** rokkovach  
**Status:** Draft

---

## 1. Problem Statement

Non-technical coworkers need to analyze sensitive textual data (PII, proprietary, regulated) using word embeddings. Cloud-based APIs are not an option. They need a simple CLI tool that:

- Reads data from Excel files (`.xlsx`)
- Generates embeddings locally (no data leaves the machine)
- Finds nearest neighbors using similarity/distance metrics
- Supports composite keys built from multiple columns

Target hardware: Apple Silicon Macs with 16 GB unified memory.

---

## 2. Users & Personas

| Persona | Description | Needs |
|---------|-------------|-------|
| **Analyst (primary)** | Non-technical business user | Simple CLI commands, clear output, Excel I/O |
| **Power User** | Comfortable with terminal, some Python | Configurable models, custom metrics, scripting |

No coding ability is assumed for the primary persona. Commands must be copy-paste friendly with sensible defaults.

---

## 3. Goals & Non-Goals

### Goals

- Zero data egress — all computation runs locally
- One-command install via `pip`
- Sub-5-minute time-to-first-result from install
- Support datasets up to 100K rows on 16 GB RAM
- Deterministic, reproducible results
- Output results to `.xlsx` for downstream consumption

### Non-Goals

- Real-time / streaming processing
- Training or fine-tuning custom embedding models
- Web UI or REST API
- GPU-only models (must work on Apple Silicon CPU/MPS)
- Vector database integration (FAISS, Chroma, etc.)

---

## 4. Architecture Overview

```
index_numerorum/
├── PRDs/                    # Product requirements
├── src/
│   └── index_numerorum/
│       ├── __init__.py
│       ├── cli.py           # Typer CLI entry point
│       ├── io.py            # XLSX read/write
│       ├── embed.py         # Embedding generation
│       ├── keys.py          # Composite key construction
│       ├── similarity.py    # Distance & similarity metrics
│       ├── neighbors.py     # Nearest-neighbor search
│       └── config.py        # Model registry & defaults
├── tests/
│   ├── conftest.py
│   ├── test_embed.py
│   ├── test_similarity.py
│   ├── test_neighbors.py
│   └── test_keys.py
├── pyproject.toml
├── README.md
└── .gitignore
```

### Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.11+ | Broad compatibility, ML ecosystem |
| CLI | [Typer](https://typer.tiangolo.com/) | Type-hinted, auto-docs, rich output |
| Embeddings | sentence-transformers | Default, proven, 400+ models |
| Excel I/O | openpyxl | Read/write `.xlsx` without Excel |
| Data | pandas | Column selection, filtering, joins |
| Numerics | NumPy | Vector math |
| Progress | Rich | Progress bars, formatted tables in terminal |
| Packaging | hatch or setuptools via pyproject.toml | Modern Python packaging |

---

## 5. Embedding Models

The tool supports multiple local models. All run on CPU + Apple MPS. Models are downloaded once and cached locally via HuggingFace `~/.cache/huggingface/`.

### Default Model

| Model | Dim | Size | Why |
|-------|-----|------|-----|
| `all-MiniLM-L6-v2` | 384 | ~80 MB | Fast, good quality, fits all machines. Default for first-time users. |

### Recommended Models (16 GB Macs)

| Model | Dim | Size | Notes |
|-------|-----|------|-------|
| `BAAI/bge-large-en-v1.5` | 1024 | ~1.3 GB | Top MTEB scores, excellent quality |
| `nomic-ai/nomic-embed-text-v1.5` | 768 | ~550 MB | State-of-the-art, long context (8192 tokens) |
| `Alibaba-NLP/gte-large-en-v1.5` | 1024 | ~1.3 GB | Cutting-edge, top MTEB rankings |
| `intfloat/e5-large-v2` | 1024 | ~1.3 GB | Strong performer, well-tested |

### Model Selection Logic

```bash
# Use default (lightweight)
index-numerorum embed data.xlsx --column "Description"

# Use a specific model
index-numerorum embed data.xlsx --column "Description" --model "BAAI/bge-large-en-v1.5"

# List available models
index-numerorum models
```

---

## 6. Features & CLI Commands

### 6.1 `index-numerorum embed`

Read an `.xlsx` file, generate embeddings for selected columns, and save an enriched `.xlsx` file (or intermediate `.parquet` for large datasets).

```bash
index-numerorum embed INPUT.xlsx \
  --column "Product Name" \
  --column "Category" \
  --model "all-MiniLM-L6-v2" \
  --output embedded_output.xlsx
```

**Behavior:**
- Validates input file exists and is `.xlsx`
- Shows progress bar during embedding generation
- Appends embedding vectors as JSON strings in new columns (e.g., `_emb_Product Name`)
- Supports `--batch-size` for memory control (default: 64)

### 6.2 `index-numerorum neighbors`

Find nearest neighbors for every row (or a subset) using a chosen similarity metric.

```bash
index-numerorum neighbors embedded_output.xlsx \
  --key "Product Name" \
  --metric cosine \
  --top-k 10 \
  --output neighbors.xlsx
```

**Output format (`.xlsx`):**

| query_key | neighbor_key | rank | similarity | distance |
|-----------|-------------|------|-----------|----------|
| Widget A  | Widget B    | 1    | 0.98      | 0.02     |
| Widget A  | Widget C    | 2    | 0.87      | 0.13     |

**Supported metrics:**

| Metric | Formula | Range | Sort |
|--------|---------|-------|------|
| `cosine` | `1 - (a·b)/(‖a‖‖b‖)` | [-1, 1] | Descending |
| `euclidean` | `‖a - b‖₂` | [0, ∞) | Ascending |
| `manhattan` | `‖a - b‖₁` | [0, ∞) | Ascending |
| `dot` | `a·b` | (-∞, ∞) | Descending |

### 6.3 `index-numerorum compare`

Compare two specific items directly.

```bash
index-numerorum compare embedded_output.xlsx \
  --item "Widget A" \
  --item "Widget B" \
  --key "Product Name" \
  --metric cosine
```

**Output:** Rich table showing all four metrics for the pair.

### 6.4 `index-numerorum models`

List available/downloaded models and their status.

```bash
index-numerorum models
index-numerorum models --download "BAAI/bge-large-en-v1.5"
```

### 6.5 `index-numerorum compose-key`

Build a composite key from multiple columns with a chosen strategy, then generate embeddings from the composite.

```bash
index-numerorum compose-key INPUT.xlsx \
  --columns "First Name" "Last Name" \
  --strategy concatenate \
  --separator " " \
  --output composed.xlsx
```

**Composite Key Strategies:**

| Strategy | How it works | When to use |
|----------|-------------|-------------|
| `concatenate` | Join column values with a separator → embed the resulting string | Columns are semantically related text |
| `average` | Embed each column independently → average the vectors | Columns are independent signals of equal importance |
| `weighted-average` | Embed each column independently → weighted average of vectors | Columns have different importance (e.g., title > category) |

```bash
# Weighted average example
index-numerorum compose-key INPUT.xlsx \
  --columns "Title:0.7" "Abstract:0.3" \
  --strategy weighted-average \
  --output composed_weighted.xlsx
```

---

## 7. Composite Key Feature — Detailed Design

### User Flow

1. User has an `.xlsx` with columns like: `First Name`, `Last Name`, `Department`, `Role`
2. User selects 2+ columns to compose a key
3. User picks a strategy: `concatenate`, `average`, or `weighted-average`
4. Tool generates a new `_composite_key` column and (optionally) embeds it

### Key Construction

**Concatenate:**
```
Input:  First Name="Jane", Last Name="Doe"
Output: _composite_key = "Jane Doe"
```

**Average:**
```
Input:  First Name="Jane", Last Name="Doe"
Step 1: emb_first = embed("Jane"), emb_last = embed("Doe")
Step 2: _composite_vector = (emb_first + emb_last) / 2
```

**Weighted Average:**
```
Input:  Role="Manager" (w=0.7), Department="Sales" (w=0.3)
Step 1: emb_role = embed("Manager"), emb_dept = embed("Sales")
Step 2: _composite_vector = 0.7 * emb_role + 0.3 * emb_dept
```

### Pipeline Integration

```bash
# Full pipeline: compose key → embed → find neighbors
index-numerorum compose-key staff.xlsx \
  --columns "First Name" "Last Name" \
  --strategy concatenate \
  --embed \
  --model "all-MiniLM-L6-v2" \
  --output staff_composed.xlsx

index-numerorum neighbors staff_composed.xlsx \
  --key "_composite_key" \
  --top-k 5 \
  --metric cosine \
  --output staff_neighbors.xlsx
```

---

## 8. Data Flow

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│  INPUT.xlsx │───▶│ compose-key  │───▶│     embed       │───▶│ EMBEDDED.xlsx│
│             │    │ (optional)   │    │                 │    │              │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────┬───────┘
                                                                    │
                                              ┌─────────────────────┘
                                              ▼
                                     ┌──────────────┐    ┌───────────────────┐
                                     │   neighbors  │───▶│ NEIGHBORS.xlsx    │
                                     │   compare    │    │ COMPARE result    │
                                     └──────────────┘    └───────────────────┘
```

---

## 9. Performance Requirements

| Scenario | Dataset Size | Model | Target Time | Memory |
|----------|-------------|-------|-------------|--------|
| Small | 1K rows | `all-MiniLM-L6-v2` | < 10s | < 2 GB |
| Medium | 10K rows | `bge-large-en-v1.5` | < 2 min | < 6 GB |
| Large | 100K rows | `all-MiniLM-L6-v2` | < 10 min | < 10 GB |
| Large | 100K rows | `bge-large-en-v1.5` | < 20 min | < 14 GB |

Neighbor search is brute-force O(n²) — acceptable up to 100K rows. For larger datasets, recommend subsampling or pre-filtering.

---

## 10. Error Handling

| Error | Message | Recovery |
|-------|---------|----------|
| File not found | `Error: 'data.xlsx' not found.` | Suggest `ls` to list files |
| Column not in file | `Error: Column 'Foo' not found. Available: A, B, C` | List available columns |
| Model not downloaded | `Model 'X' not found locally. Download? [y/n]` | Auto-prompt to download |
| OOM during embedding | `Out of memory with batch_size=64. Try --batch-size 16` | Suggest smaller batch |
| No embeddings in file | `Error: No embedded columns found. Run 'embed' first.` | Suggest correct command |

---

## 11. Installation & Quick Start

```bash
# Install
pip install index-numerorum

# Or from source
git clone https://github.com/rokkovach/index_numerorum.git
cd index_numerorum
pip install -e ".[dev]"

# Quick start
index-numerorum embed sensitive_data.xlsx --column "Description"
index-numerorum neighbors embedded_sensitive_data.xlsx --key "Description" --top-k 5
```

### Dependencies

```
typer[all]>=0.12
rich>=13.0
sentence-transformers>=3.0
torch>=2.0
openpyxl>=3.1
pandas>=2.0
numpy>=1.24
```

---

## 12. Milestones

### Phase 1 — MVP (Week 1-2)
- [ ] Project scaffolding (pyproject.toml, CLI skeleton)
- [ ] `embed` command with sentence-transformers
- [ ] `neighbors` command with cosine similarity
- [ ] `.xlsx` read/write
- [ ] Default model (`all-MiniLM-L6-v2`)

### Phase 2 — Core Features (Week 3-4)
- [ ] All four distance metrics
- [ ] `compose-key` with concatenate + average strategies
- [ ] `compare` command
- [ ] `models` command (list, download)
- [ ] Progress bars and rich output
- [ ] Error handling with helpful messages

### Phase 3 — Polish (Week 5-6)
- [ ] Weighted-average composite strategy
- [ ] Additional cutting-edge models in registry
- [ ] Parquet intermediate format for large datasets
- [ ] Tests (unit + integration)
- [ ] README with examples
- [ ] Memory usage optimization for large datasets

---

## 13. Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Should we support CSV input in addition to XLSX? | Deferred — XLSX first |
| 2 | Max dataset size before we need approximate NN (FAISS)? | Benchmarks in Phase 3 |
| 3 | Should embeddings be cached to avoid recomputation? | Yes — via intermediate files |
| 4 | Multi-language support for non-English text? | Use multilingual models (`paraphrase-multilingual`) |
| 5 | Should we support custom model paths (local .bin)? | Nice-to-have, Phase 3 |
