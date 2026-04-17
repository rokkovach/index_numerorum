# PRD 002: DX/UX Polish, Testing & Documentation

## Making Index Numerorum a 10/10 Developer & User Experience

**Version:** 1.0  
**Date:** 2026-04-17  
**Author:** rokkovach  
**Status:** Draft  
**Depends on:** PRD 001

---

## 1. Purpose

PRD 001 defined what the tool does. This PRD defines how it *feels*. The goal is a 10/10 experience across every dimension:

| Dimension | Current (PRD 001) | Target | Gap |
|-----------|-------------------|--------|-----|
| **Install experience** | `pip install` | 10/10 | Need zero-config first run |
| **CLI discoverability** | Commands listed | 10/10 | Need rich help, examples, validation |
| **Error messages** | Table of errors | 10/10 | Need prescriptive, actionable messages |
| **Output quality** | XLSX files | 10/10 | Need formatted, color-coded, self-documenting |
| **Testing** | Not addressed | 10/10 | Need comprehensive test suite |
| **Documentation** | Not addressed | 10/10 | Need world-class README |
| **Onboarding** | Quick start section | 10/10 | Need 60-second wow moment |

---

## 2. Critique & Improvements by Dimension

### 2.1 Install Experience — 10/10 Target

**Critique of PRD 001:**
- `pip install index-numerorum` is good but what happens after? User stares at a prompt.
- No version check, no welcome, no sanity check for dependencies (torch is large).
- sentence-transformers pulls PyTorch (~2 GB). First install will be slow. User needs feedback.

**Improvements:**

```
┌──────────────────────────────────────────────────────┐
│  Index Numerorum — Local Embedding Toolkit v0.1.0    │
│                                                      │
│  ✓ Python 3.12 detected                              │
│  ✓ PyTorch 2.4.0 installed (MPS available)           │
│  ✓ sentence-transformers 3.4.0 installed              │
│  ✓ Model 'all-MiniLM-L6-v2' cached (80 MB)           │
│                                                      │
│  Quick start:                                        │
│    index-numerorum embed your_file.xlsx -c "Name"    │
│    index-numerorum --help                            │
└──────────────────────────────────────────────────────┘
```

- `index-numerorum doctor` command: checks Python version, torch, MPS availability, disk space, cached models
- First-run detection: if no model cached, prompt to download the default with size estimate
- `--quiet` flag for scripting use cases

### 2.2 CLI Discoverability — 10/10 Target

**Critique of PRD 001:**
- Commands are listed but help text is generic
- No examples in `--help` output
- No autocompletion setup
- Column selection could be confusing (what if columns have spaces?)

**Improvements:**

Every command gets:
1. **Rich help panel** with description, examples, and common pitfalls
2. **Auto-detection**: if user passes an `.xlsx` file, peek at headers and suggest columns
3. **Interactive fallback**: if required args are missing, enter interactive mode (Typer `prompt`)

```bash
$ index-numerorum embed --help

 Usage: index-numerorum embed [OPTIONS] INPUT

 Generate embeddings for one or more columns in an Excel file.

╭─ Arguments ───────────────────────────────────────────────────╮
│ *  input    PATH  [default: None] [required]                  │
╰───────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────╮
│ *  --column  -c    TEXT  Column(s) to embed [required]        │
│    --model   -m    TEXT  Embedding model [default: mini]      │
│    --output  -o    PATH  Output file [default: <input>_emb]   │
│    --batch-size     INT   Batch size [default: 64]            │
╰───────────────────────────────────────────────────────────────╯
╭─ Examples ────────────────────────────────────────────────────╮
│                                                                │
│  # Single column                                               │
│  index-numerorum embed data.xlsx -c "Product Name"            │
│                                                                │
│  # Multiple columns (separate embeddings per column)           │
│  index-numerorum embed data.xlsx -c "Name" -c "Description"   │
│                                                                │
│  # Specify model                                               │
│  index-numerorum embed data.xlsx -c "Name" -m bge-large       │
│                                                                │
╰───────────────────────────────────────────────────────────────╯

 Model shortcuts: mini (all-MiniLM-L6-v2), bge-large, nomic, gte, e5
```

**Model shortcuts** (critical for non-technical users — they don't know HuggingFace model IDs):

| Shortcut | Full Model ID |
|----------|--------------|
| `mini` | `all-MiniLM-L6-v2` |
| `bge-large` | `BAAI/bge-large-en-v1.5` |
| `nomic` | `nomic-ai/nomic-embed-text-v1.5` |
| `gte` | `Alibaba-NLP/gte-large-en-v1.5` |
| `e5` | `intfloat/e5-large-v2` |

### 2.3 Error Messages — 10/10 Target

**Critique of PRD 001:**
- Error table is a good start but messages are too terse
- No error codes, no suggestions for fix, no color
- No handling of "XLSX is open in Excel" (file lock)

**Improvements — Error Message Formula:**

Every error follows this structure:

```
╭─ Error ───────────────────────────────────────────╮
│  [ICON] What happened                              │
│                                                    │
│  Why it happened                                   │
│                                                    │
│  How to fix it:                                    │
│    1. Step one                                     │
│    2. Step two                                     │
╰────────────────────────────────────────────────────╯
```

**Concrete examples:**

```
╭─ Error ──────────────────────────────────────────────────────╮
│  File 'data.xlsx' is locked                                   │
│                                                               │
│  The file is currently open in another application (Excel?).  │
│                                                               │
│  How to fix:                                                  │
│    1. Close Excel                                             │
│    2. Or use --output to write to a different file            │
╰──────────────────────────────────────────────────────────────╯

╭─ Error ──────────────────────────────────────────────────────╮
│  Column 'Desription' not found                                │
│                                                               │
│  Did you mean one of these?                                   │
│    • "Description"  (相似的列名)                               │
│    • "Designation"                                             │
│                                                               │
│  Available columns: ID, Name, Description, Category, Price    │
╰──────────────────────────────────────────────────────────────╯

╭─ Error ──────────────────────────────────────────────────────╮
│  Out of memory while embedding row 45,000                     │
│                                                               │
│  Your dataset (50K rows × 1024 dims) needs ~390 MB of RAM    │
│  for the similarity matrix. Your batch_size=64 uses ~12 GB.   │
│                                                               │
│  How to fix:                                                  │
│    1. Reduce batch size: --batch-size 16                      │
│    2. Use a smaller model: -m mini (384 dims vs 1024)         │
│    3. Close other applications to free memory                  │
╰──────────────────────────────────────────────────────────────╯
```

**Fuzzy column matching:** Use `difflib.get_close_matches()` to suggest typos.

### 2.4 Output Quality — 10/10 Target

**Critique of PRD 001:**
- Output format is a plain table. Not bad but not 10/10.
- No summary statistics on the output
- No inline visualization of similarity distribution
- Embedding vectors stored as JSON strings — unreadable in Excel

**Improvements:**

**Terminal output after `neighbors`:**

```
$ index-numerorum neighbors embedded.xlsx -k "Name" --top-k 5

╭─ Nearest Neighbors ──────────────────────────────────────╮
│  Key column: Name    Metric: cosine    Top-K: 5           │
│  Dataset: 1,247 rows    Model: all-MiniLM-L6-v2           │
│  Elapsed: 3.2s                                            │
╰───────────────────────────────────────────────────────────╯

 Top neighbors for "Widget A"
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #  Name         Similarity   Visual
 ──  ───────────  ──────────  ─────────────────────────
  1  Widget B         0.98    ████████████████████░░
  2  Widget C         0.87    █████████████████░░░░░
  3  Widget D         0.82    ████████████████░░░░░░
  4  Widget E         0.71    ██████████████░░░░░░░░
  5  Widget F         0.65    ████████████░░░░░░░░░░

 Showing 5 / 1,247 neighbors. Full results in neighbors.xlsx
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Excel output improvements:**
- Header row: bold, frozen, light gray background
- Similarity column: conditional formatting (green = high, yellow = mid, red = low)
- New sheet: `_metadata` with run parameters (model, metric, date, input file, column)
- New sheet: `_stats` with distribution stats (mean, median, std, min, max similarity)
- Embedding vectors: stored in a hidden sheet (not the main sheet) to keep the output clean

### 2.5 Onboarding — The 60-Second Wow Moment

**Critique of PRD 001:**
- Quick start exists but assumes the user has a file ready
- No sample data, no guided walkthrough

**Improvements:**

`index-numerorum demo` command:

```bash
$ index-numerorum demo

╭─ Index Numerorum Demo ────────────────────────────────────╮
│  Creating sample dataset with 50 products...               │
│  Embedding with all-MiniLM-L6-v2...                        │
│  Finding nearest neighbors (cosine)...                      │
│                                                             │
│  ✓ Demo complete! Files created in ./demo_output/          │
│    • demo_products.xlsx    (source data)                    │
│    • demo_embedded.xlsx    (data + embeddings)              │
│    • demo_neighbors.xlsx   (nearest neighbor results)       │
│                                                             │
│  Try it yourself:                                           │
│    index-numerorum embed demo_products.xlsx -c "Name"      │
╰───────────────────────────────────────────────────────────╯
```

This gives users a working example they can open in Excel immediately.

---

## 3. Testing Strategy — 10/10

### 3.1 Principles

1. **No network in CI** — Tests must not download models. Use fixtures with pre-computed vectors.
2. **Fast** — Full test suite runs in < 30 seconds (excluding integration tests).
3. **Deterministic** — No flaky tests, no floating-point comparisons without tolerance.
4. **Coverage target** — 90%+ line coverage on `src/`.

### 3.2 Test Architecture

```
tests/
├── conftest.py              # Shared fixtures (sample DataFrames, mock embeddings)
├── unit/
│   ├── test_similarity.py   # Distance metrics (pure math, no models)
│   ├── test_keys.py         # Composite key construction
│   ├── test_io.py           # XLSX read/write
│   ├── test_config.py       # Model registry, shortcuts
│   └── test_cli.py          # CLI argument parsing, validation
├── integration/
│   ├── test_embed_pipeline.py   # End-to-end embed (with tiny model)
│   ├── test_neighbor_pipeline.py
│   └── test_compose_pipeline.py
└── fixtures/
    ├── sample.xlsx          # 20-row test dataset
    ├── sample_embedded.xlsx # Same data with pre-computed embeddings
    └── expected_vectors.npy # Pre-computed vectors for assertions
```

### 3.3 Test Matrix

#### Unit Tests — `test_similarity.py`

```
TestCosineSimilarity:
  ✓ identical vectors → 1.0
  ✓ orthogonal vectors → 0.0
  ✓ opposite vectors → -1.0
  ✓ known pair → expected value (within 1e-6)
  ✓ zero vector → raises ValueError
  ✓ batch computation matches pairwise

TestEuclideanDistance:
  ✓ identical vectors → 0.0
  ✓ unit orthogonal → 1.414
  ✓ scaling invariance check
  ✓ batch computation matches pairwise

TestManhattanDistance:
  ✓ identical vectors → 0.0
  ✓ unit basis vectors → 2.0
  ✓ batch computation matches pairwise

TestDotProduct:
  ✓ orthogonal vectors → 0.0
  ✓ unit vectors → cosine * magnitude
  ✓ batch computation matches pairwise
```

#### Unit Tests — `test_keys.py`

```
TestConcatenateStrategy:
  ✓ two columns joined with space
  ✓ custom separator
  ✓ handles NaN → empty string
  ✓ three columns

TestAverageStrategy:
  ✓ two equal vectors → same vector
  ✓ two different vectors → mean
  ✓ handles NaN column → skip or zero
  ✓ single column → same as direct embed

TestWeightedAverageStrategy:
  ✓ weights sum to 1.0 → correct weighted mean
  ✓ weights don't sum to 1.0 → normalize automatically
  ✓ single column with any weight → same vector
  ✓ zero-weight column → excluded
  ✓ invalid weight string → raises ValueError
```

#### Unit Tests — `test_io.py`

```
TestReadXLSX:
  ✓ reads valid file → DataFrame
  ✓ file not found → FileNotFoundError with message
  ✓ non-xlsx file → raises with clear message
  ✓ empty file → raises with message
  ✓ file with no data rows → raises with message

TestWriteXLSX:
  ✓ writes DataFrame → readable file
  ✓ output file exists → overwrite with warning
  ✓ file locked (if testable) → clear error
  ✓ metadata sheet present
```

#### Unit Tests — `test_config.py`

```
TestModelRegistry:
  ✓ shortcut 'mini' → correct model ID
  ✓ shortcut 'bge-large' → correct model ID
  ✓ unknown shortcut → suggestion
  ✓ full model ID → pass-through
  ✓ model dimensions match registry

TestModelDownload:
  ✓ model exists locally → no download
  ✓ model not local → prompt message generated
```

#### Unit Tests — `test_cli.py`

```
TestEmbedCommand:
  ✓ missing input → error with usage
  ✓ missing --column → error with usage
  ✓ invalid model shortcut → suggestion
  ✓ input is directory → clear error

TestNeighborsCommand:
  ✓ no embedded columns found → error suggesting embed
  ✓ invalid metric → list valid metrics
  ✓ top-k > dataset size → clamp + warning

TestComposeKeyCommand:
  ✓ single column → warning (no need for compose)
  ✓ empty column list → error
  ✓ invalid strategy → list valid strategies
```

#### Integration Tests

```
TestEmbedPipeline:
  ✓ sample.xlsx → embedded.xlsx with correct shape
  ✓ embedding column names follow convention
  ✓ metadata sheet present and correct
  ✓ batch-size affects memory (mocked)

TestNeighborPipeline:
  ✓ embedded input → neighbor output with correct columns
  ✓ top-k respected
  ✓ metric affects ordering (cosine vs euclidean)
  ✓ self-neighbor excluded or at rank 0

TestFullPipeline:
  ✓ compose → embed → neighbors → valid output
  ✓ compare command → all four metrics present
  ✓ demo command → three output files created
```

### 3.4 CI Pipeline

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/unit -v --tb=short
      - run: pytest tests/integration -v --tb=short
      - run: ruff check src/ tests/
      - run: mypy src/

  # macOS runner for MPS validation
  test-mac:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --tb=short
```

### 3.5 Testing Tools

| Tool | Purpose |
|------|---------|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `pytest-mock` | Mocking (especially model downloads) |
| `numpy.testing` | Array comparisons with tolerance |
| `freezegun` | Time-dependent tests (metadata timestamps) |
| `ruff` | Linting + formatting |
| `mypy` | Type checking |

### 3.6 Dev Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-mock>=3.14",
    "ruff>=0.5",
    "mypy>=1.10",
]
```

---

## 4. README — 10/10

The README is the most important artifact. Non-technical users will read this and decide if the tool is worth trying. It must be:

- **Scannable** — someone should understand the tool in 10 seconds
- **Copy-pasteable** — every example works verbatim
- **Visual** — use code blocks, tables, and diagrams
- **Honest** — state limitations upfront

### README Structure

```markdown
# Index Numerorum

> Local embeddings for sensitive data. No cloud. No API keys. No data leaving your machine.

[One-line install → one-command results → Excel output your team already knows.]

## Install

## 60-Second Demo

## What It Does

## Commands

## Examples (Real Workflows)

## Models

## FAQ

## Limitations
```

### Full README Text

See the README artifact in the implementation phase. Key principles:

1. **Above the fold** (first screen): Install command + demo command. Nothing else. If the user only reads this far, they can try the tool.

2. **What It Does**: 3-sentence description. One ASCII diagram showing the flow.

3. **Commands**: A table, not prose. One command per row with the most common flags.

4. **Examples**: Real-world workflows with actual filenames and column names. Not `foo/bar` — use `employees.xlsx`, `products.xlsx`, `contracts.xlsx`.

5. **Models**: Table with shortcut, full name, size, quality tier. Non-technical users pick from a menu.

6. **FAQ**: Pre-empt the 5 questions users will definitely ask:
   - "Is my data safe?" → Yes, everything is local.
   - "Do I need a GPU?" → No, runs on any Mac with 16 GB.
   - "How long does it take?" → Table with estimates.
   - "Can I use this for [X]?" → Guidance on appropriate use cases.
   - "The first run is slow?" → Yes, downloading the model. Subsequent runs are fast.

7. **Limitations**: Honest. 100K row practical limit. No GPU-only models. English models by default.

---

## 5. Additional DX Tightening

### 5.1 Smart Defaults Everywhere

Non-technical users should never have to think about:

| Decision | Default | Override |
|----------|---------|----------|
| Model | `mini` (fast, small) | `--model bge-large` |
| Metric | `cosine` | `--metric euclidean` |
| Top-K | `10` | `--top-k 50` |
| Batch size | `64` | `--batch-size 16` |
| Output file | `{input}_embedded.xlsx` | `--output custom.xlsx` |
| Separator (compose) | `" "` (space) | `--separator ", "` |

### 5.2 Progress That Means Something

Not just a spinner. Show:

```
Embedding rows... ━━━━━━━━━━━━━━━━━━ 3,421/5,000 68% 0:00:42
  Model: all-MiniLM-L6-v2  |  Batch: 64  |  Speed: ~80 rows/s  |  ETA: 0:00:20
```

### 5.3 Idempotency

- Re-running `embed` on an already-embedded file should skip or warn, not double-embed
- Column naming convention: `_emb_{column_name}` — detect and skip if present
- `--force` flag to re-embed

### 5.4 Column Name Handling

Columns with spaces, special characters, and Unicode must work:

```bash
# All of these should work:
index-numerorum embed data.xlsx -c "Product Name"
index-numerorum embed data.xlsx -c "Ürün Adı"
index-numerorum embed data.xlsx -c "Product/Service (EN)"
```

### 5.5 Output File Safety

- Never overwrite the input file (default output is `{stem}_embedded.xlsx`)
- If output exists, prompt: `Overwrite 'output.xlsx'? [y/N]`
- `--force` to skip prompt

### 5.6 Version & Reproducibility

Every output file gets a `_metadata` sheet containing:

| Key | Value |
|-----|-------|
| `tool` | `index-numerorum` |
| `version` | `0.1.0` |
| `command` | `embed data.xlsx -c "Name" -m mini` |
| `model` | `all-MiniLM-L6-v2` |
| `model_dim` | `384` |
| `python` | `3.12.3` |
| `torch` | `2.4.0` |
| `date` | `2026-04-17T14:32:01` |
| `input_file` | `data.xlsx` |
| `input_rows` | `1247` |
| `input_md5` | `a1b2c3...` |

This ensures any output can be reproduced.

---

## 6. Implementation Priority

Ordered by impact on the non-technical user experience:

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | README (sections 1-4) | 2h | Highest — first thing anyone sees |
| P0 | `demo` command | 2h | Highest — instant wow moment |
| P0 | Rich error messages with suggestions | 3h | Highest — prevents frustration |
| P1 | Unit tests for similarity module | 2h | High — correctness foundation |
| P1 | Model shortcuts | 1h | High — removes HuggingFace knowledge barrier |
| P1 | Smart defaults + idempotency | 2h | High — prevents footguns |
| P1 | Progress bars with ETA | 1h | Medium — trust & transparency |
| P2 | Excel formatting (colors, metadata sheet) | 3h | Medium — professional output |
| P2 | Full test suite (unit + integration) | 4h | Medium — reliability |
| P2 | CI pipeline | 1h | Medium — safety net |
| P2 | `doctor` command | 1h | Low — troubleshooting |
| P3 | README FAQ + Limitations | 1h | Low — reduces support burden |
| P3 | Fuzzy column matching | 1h | Low — nice to have |

---

## 7. Success Metrics

The tool is a 10/10 DX/UX when:

- [ ] A non-technical user can go from `pip install` to seeing results in < 5 minutes
- [ ] No user ever needs to read source code to figure out how to use the tool
- [ ] Every error message contains the fix
- [ ] Every output file is self-documenting (metadata sheet)
- [ ] `index-numerorum --help` is sufficient documentation for all commands
- [ ] `index-numerorum demo` produces a working example in < 30 seconds
- [ ] Test suite passes in < 30 seconds with 90%+ coverage
- [ ] No flaky tests, no network-dependent tests in CI
