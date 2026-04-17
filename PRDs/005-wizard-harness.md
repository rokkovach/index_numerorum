# PRD 005: Wizard Mode & Interactive Harness

**Date:** 2026-04-17
**Status:** Executed
**Depends on:** PRD 001, 002, 003, 004

## Problem

The current CLI is power-user friendly but intimidating for non-technical coworkers:

1. They must know the exact command pipeline (embed -> neighbors -> output)
2. They must type column names exactly, know model shortcuts, remember flags
3. There's no guided path from "I have an xlsx file" to "here are my results"
4. Files live wherever the user remembers to put them — no convention
5. **No visual feedback during processing** — the user stares at a blank screen while embedding/neighbors run, with no sense of progress or activity

## Solution

### 1. Drop-and-Run Flow

User drops files into `input/`, runs the command, and the wizard handles everything:

```
$ index-numerorum

  ╔════════════════════════════════════════════════╗
  ║          Index Numerorum v0.1.0                ║
  ║        Local Embedding Toolkit                 ║
  ╚════════════════════════════════════════════════╝

  Scanning input/ ...

  Found 3 files:
    [1] products.xlsx        (247 rows, 5 columns)
    [2] staff_q1.xlsx        (52 rows, 8 columns)
    [3] vendor_catalog.xlsx  (1,200 rows, 12 columns)

  Select a file [1-3]: 1
```

If no files found, shows a friendly message:
```
  No .xlsx files found in input/
  Drop your Excel files into the input/ folder and try again.
```

### 2. Column Wizard

After file selection, inspect and guide:

```
  ┌─ Column Selection ─────────────────────────────┐
  │                                                  │
  │  Columns in products.xlsx:                       │
  │                                                  │
  │    [1] Product ID    🔑 247 unique values        │
  │    [2] Product Name  📝 text                     │
  │    [3] Category      📝 4 unique values          │
  │    [4] Price         #   numeric                  │
  │    [5] Description   📝 text                     │
  │                                                  │
  │  Select KEY column (or press Enter to auto-generate IDs): 1        │
  │  Select column(s) to EMBED: 2,5                                    │
  │                                                  │
  └──────────────────────────────────────────────────┘
```

Columns auto-flagged with icons:
- `key` icon for likely-key columns (all unique, no nulls)
- `text` icon for text columns
- `#` for numeric

### 3. Model Selection

```
  Select model:
    [1] mini       (~80 MB)   Fast, good quality          ★ recommended
    [2] bge-large  (~1.3 GB)  Top accuracy
    [3] nomic      (~550 MB)  Long context
    [4] gte        (~1.3 GB)  Cutting-edge
    [5] e5         (~1.3 GB)  Well-tested

  Model [1]: 1
```

### 4. Visual Processing Feedback — The Core Improvement

Every long-running operation shows rich, animated visual feedback. The user should
**never stare at a blank screen** during processing.

#### Embedding Progress

```
  ┌─ Running ───────────────────────────────────────┐
  │                                                  │
  │  File:    products.xlsx (247 rows)               │
  │  Key:     Product ID                             │
  │  Embed:   Product Name + Description             │
  │  Model:   all-MiniLM-L6-v2                       │
  │                                                  │
  └──────────────────────────────────────────────────┘

  ⠋ Loading model all-MiniLM-L6-v2 ...
  ✓ Model loaded (1.2s)

  Embedding 247 rows ━━━━━━━━━━━━━━━━━━━━ 67% 166/247  0:00:03

  ✓ Embedding complete (4.2s)

  Computing similarities ━━━━━━━━━━━━━━━━ 100% 247/247  0:00:01

  ✓ Found 2,470 neighbor pairs (1.8s)

  Writing output/products_neighbors.xlsx ...
  ✓ Written (0.3s)
```

Visual elements during processing:
- **Spinner** during model loading (indeterminate phase)
- **Progress bar** with count and ETA during embedding (batch-by-batch)
- **Progress bar** during neighbor computation
- **Tick marks** with timing after each phase completes
- **Summary panel** at the end

#### Summary Panel

```
  ┌─ Complete ──────────────────────────────────────┐
  │                                                  │
  │  ✓ 247 rows embedded                             │
  │  ✓ 2,470 neighbor pairs found                    │
  │  ✓ Results saved to output/products_neighbors.xlsx│
  │                                                  │
  │  Total time: 7.3s                                │
  │                                                  │
  └──────────────────────────────────────────────────┘
```

#### Visual Feedback Requirements (applies to ALL commands, not just wizard)

| Phase | Visual | When |
|-------|--------|------|
| Model loading | Spinner + "Loading model..." | Any command that loads a model |
| Embedding | Progress bar (rows / total), ETA | `embed`, `run`, `store init`, `store add` |
| Neighbor computation | Progress bar (pairs / total), ETA | `neighbors`, `run` |
| Store match | Progress bar (pairs / total) | `store match` |
| Writing xlsx | Spinner + "Writing..." | Any command that writes output |
| Store creation | Spinner + "Creating store..." | `store init` |
| Each phase complete | Green tick + timing | Always |

### 5. Post-Run Menu

```
  What next?
    [1] Open output folder
    [2] Run again with different settings
    [3] Store match (find duplicates above threshold)
    [4] Done

  Choice: 4
```

### 6. Folder Convention

```
./
  input/       ← drop xlsx files here
  output/      ← results land here
```

- `index-numerorum` auto-creates both folders on first run
- Output naming: `{stem}_neighbors.xlsx`, `{stem}_embedded.xlsx`
- If only 1 file in `input/`, auto-select it (skip file selection)

### 7. `--quick` Mode

```bash
index-numerorum --quick
```

Minimal prompts — uses defaults for everything not ambiguous:
- If only 1 file in `input/`, auto-select it
- If only 1 text column, auto-select as embed column
- Auto-detect key column (first column with all unique values)
- Use `mini` model, cosine metric, top-10 neighbors
- Still shows full visual progress feedback

### 8. Bare Invocation = Harness

`index-numerorum` with no subcommand launches the wizard directly. All existing
subcommands (`embed`, `neighbors`, `compare`, etc.) still work as before.

## Wizard Steps

| Step | Visual | Input |
|------|--------|-------|
| **Scan** | Spinner "Scanning input/..." then file list table | File number (auto if 1 file) |
| **Inspect** | Rich table with column icons and type hints | — |
| **Key column** | Highlighted likely-key columns; option to auto-generate (`_row_id`) | Column number, or "auto" to generate sequential IDs |
| **Embed columns** | Highlighted text columns | Column numbers (auto if 1 text col) |
| **Model** | Model table with recommended star | Model number (default: mini) |
| **Run** | Full visual pipeline (spinner + progress bars + ticks) | — |
| **Summary** | Green completion panel with stats | — |
| **Next** | Post-run menu | Choice |

## Implementation Details

### New files

| File | Purpose |
|------|---------|
| `src/index_numerorum/wizard.py` | Wizard flow, column inspection, prompt helpers |
| `src/index_numerorum/visuals.py` | Rich progress wrappers — spinner bars, phase ticks, summary panels |

### Modified files

| File | Changes |
|------|---------|
| `cli.py` | Bare invocation → wizard; add visual progress to existing `embed`, `neighbors`, `store init`, `store add` commands |
| `embed.py` | Add `batch_callback` parameter to `embed_columns` for progress bar updates |

### Column Inspection

```python
@dataclass
class ColumnInfo:
    name: str
    index: int          # 1-based for display
    dtype: str          # "text", "numeric", "datetime", "mixed"
    unique_count: int
    total_count: int
    null_count: int
    is_likely_key: bool  # all unique, no nulls
    is_likely_text: bool # string dtype, not all unique
```

### Unique ID Handling

The wizard offers three ways to assign unique IDs per row:

1. **Pick a column** — select an existing column that has unique values
2. **Auto-generate** — press Enter at the key prompt to create `_row_id` column with sequential integers (1, 2, 3, ...)
3. **Composite key** — combine multiple columns into a single key (existing `compose-key` logic)

If the user picks a column with duplicate values, the wizard warns and offers to
deduplicate or pick another column. Auto-generated IDs are written into the
embedded output so the user can trace results back to source rows.

### Visual Progress Helpers (visuals.py)

```python
class EmbedProgress:
    """Wraps sentence-transformers encode with Rich progress bar."""

class PhaseTracker:
    """Tracks multiple phases (load, embed, neighbors, write) with timing."""

def spinner_phase(console, message: str, func, *args) -> tuple[result, elapsed]:
    """Run func with a Rich spinner, return result + elapsed time."""

def completion_panel(console, phases: list[tuple[str, float]], output_path: Path):
    """Show green summary panel with phase timings and output path."""
```

### Output Naming

```
output/
  {stem}_embedded.xlsx
  {stem}_neighbors.xlsx
  {stem}_matches.xlsx
```

### Error Recovery

- Invalid selection → re-prompt with red error, never crash
- File read error → Rich error panel, return to file selection
- Model download fails → error, offer to try another model
- Ctrl+C → clean exit with "Cancelled" message

## Scope

### In scope
- Bare `index-numerorum` launches wizard
- Auto-create `input/` and `output/`
- Column inspection with type detection and heuristics
- Visual progress for ALL long-running operations (embedding, neighbors, store ops)
- `--quick` mode with auto-detection
- Post-run menu

### Deferred
- Config file for saving preferences
- Batch mode (multiple files in one run)
- Export formats beyond xlsx
- Harness session loop (menu after menu) — wizard runs once then exits

## Acceptance Criteria

1. `index-numerorum` (bare) creates `input/`/`output/` and launches wizard
2. Drop an xlsx into `input/`, run `index-numerorum`, wizard guides to results
3. Every processing phase shows a visual (spinner or progress bar + timing)
4. `--quick` auto-selects obvious choices, still shows full visuals
5. All existing subcommands still work unchanged
6. Visuals added to `embed`, `neighbors`, `store init`, `store add` commands
7. Tests: `inspect_columns`, column heuristics, output naming, wizard flow (mocked input)
8. Lint clean, no new dependencies
