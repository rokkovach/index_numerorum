# PRD 003: Terminal Output Polish

## Making every screen a delight

**Date:** 2026-04-17  
**Depends on:** PRD 001, PRD 002

---

## 1. Current State Audit

Evaluated by running every command end-to-end. Issues found:

### Critical UX Problems

| ID | Where | Problem | Severity |
|----|-------|---------|----------|
| T1 | `--help` main | Commands listed as bare words with no description | High |
| T2 | `embed` help | Examples section renders as unformatted raw text, not a proper panel | High |
| T3 | `embed` output | "Using model:" line appears before the spinner with no visual grouping | Medium |
| T4 | `embed` output | "Success!" is plain text, no summary of what was done | Medium |
| T5 | `neighbors` preview | Score column header misaligned, bar visual wedged into number column | High |
| T6 | `compare` title | Long names break the table title across lines awkwardly | Medium |
| T7 | `compare` output | No visual distinction between the highlighted metric and others | Medium |
| T8 | `compose-key` output | Just "Success!" with no summary of what key was built | Medium |
| T9 | `models` output | No description of models, users can't decide which to use | Medium |
| T10 | `demo` output | Intermediate steps printed as plain text, no unified flow | Medium |
| T11 | `doctor` output | Good but no color on the section header | Low |
| T12 | Error panels | Double-render of error text (message contains the same info as hint) | Medium |
| T13 | `neighbors` | No timing info — users don't know if it's still running | Low |

### What's Already Good

- Rich panels for errors — works well
- `doctor` table — clean and scannable
- `models` table — compact and useful
- `--version` flag — works

---

## 2. Design Spec

### 2.1 Main `--help` — Command Descriptions

Commands should have one-line descriptions, not just names.

```
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ embed        Generate embeddings for text columns                            │
│ neighbors    Find nearest neighbors for every row                            │
│ compare      Compare two specific records side-by-side                       │
│ compose-key  Build a composite key from multiple columns                     │
│ models       List or download embedding models                               │
│ demo         Run a guided demo with sample data                             │
│ doctor       Check your system environment                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Implementation:** Use Typer's `help` parameter on each `@app.command()`.

### 2.2 Help Epilogs — Proper Rich Panels

Current examples render as raw text. Fix by using `rich_markup_mode="rich"` with formatted epilog strings that use `[dim]`, `[bold]`, `[cyan]` markup in the epilog text.

Format:
```
╭─ Examples ───────────────────────────────────────────────────────────────────╮
│                                                                              │
│  [dim]# Single column[/dim]                                                  │
│  index-numerorum embed data.xlsx -c "Product Name"                           │
│                                                                              │
│  [dim]# Multiple columns[/dim]                                               │
│  index-numerorum embed data.xlsx -c "Name" -c "Description"                  │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Implementation:** Use `\n` separated strings with Rich markup. Typer renders epilots as-is in rich mode.

### 2.3 `embed` Command Output

**Before:**
```
Using model: all-MiniLM-L6-v2 (dimensions=384, size=80MB)
⠸ Done.
Success! Written to /tmp/test_data_embedded.xlsx
```

**After:**
```
╭─ Embedding ──────────────────────────────────────────────────────────────────╮
│ Model: all-MiniLM-L6-v2 (384 dims, 80 MB)                                   │
│ Columns: Name, Category                                                     │
│ Rows: 8                                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
⠋ Embedding rows...
╭─ Complete ───────────────────────────────────────────────────────────────────╮
│ ✓ 2 columns embedded (384 dims each)                                        │
│ ✓ 8 rows processed                                                          │
│ → /tmp/test_data_embedded.xlsx                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 2.4 `neighbors` Command Output

**Before:** Score and bar crammed in one column. No timing.

**After:**
```
╭─ Neighbors ──────────────────────────────────────────────────────────────────╮
│ Key: Name    Metric: cosine    Top-K: 3    Rows: 8    Pairs: 24    0.2s      │
╰──────────────────────────────────────────────────────────────────────────────╯

  Top neighbors for "Wireless Mouse"
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  #  Neighbor              Score
 ──  ────────────────────  ────────────────────────────────────────
  1  Mechanical Keyboard   0.349  ████████░░░░░░░░░░░░
  2  USB-C Hub             0.289  ██████░░░░░░░░░░░░░░
  3  Portable Charger      0.251  █████░░░░░░░░░░░░░░░

 → /tmp/test_data_embedded_neighbors.xlsx
```

Key changes:
- Score and visual bar in separate columns
- Timing info
- Cleaner header with row count
- Summary panel is a single line

### 2.5 `compare` Command Output

**Before:** Title wraps, no visual distinction.

**After:**
```
╭─ Comparison ─────────────────────────────────────────────────────────────────╮
│ "Wireless Mouse"  vs  "USB-C Hub"                                           │
│ Key: Name    Highlighted: cosine                                            │
╰──────────────────────────────────────────────────────────────────────────────╯

 Metric      Score
 ──────────  ──────────
 ● cosine    0.289365  ██████░░░░░░░░░░░░░░
   euclidean 1.192170
   manhattan 18.340519
   dot       0.289365
```

Key changes:
- Title never wraps — names go in a summary panel
- Highlighted metric has `●` prefix and green color + bar
- Other metrics are dimmed

### 2.6 `compose-key` Command Output

**Before:** Just "Success! Written to ..."

**After:**
```
╭─ Composite Key ──────────────────────────────────────────────────────────────╮
│ Columns: Name, Category                                                     │
│ Strategy: concatenate                                                       │
│ Sample: "Wireless Mouse Electronics"                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
⠋ Embedding...
╭─ Complete ───────────────────────────────────────────────────────────────────╮
│ ✓ Key built from 2 columns                                                  │
│ ✓ Embedded with all-MiniLM-L6-v2 (384 dims)                                │
│ → /tmp/test_data_composed.xlsx                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 2.7 `models` Command Output

Add back a brief description per model, but keep it one line:

```
                          Available Models                           
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━┓
┃ Shortcut  ┃ Model ID                       ┃ Dims ┃    Size ┃ Cached ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━┩
│ mini      │ all-MiniLM-L6-v2               │  384 │   80 MB │   ✗    │
│           │ Fast & lightweight              │      │         │        │
│ bge-large │ BAAI/bge-large-en-v1.5         │ 1024 │ 1300 MB │   ✗    │
│           │ Top MTEB scores                 │      │         │        │
│ ...       │                                │      │         │        │
└───────────┴────────────────────────────────┴──────┴─────────┴────────┘
```

Actually, simpler: add a description column back with `max_width=25`.

### 2.8 `demo` Command Output

**Before:** Scattered lines.

**After:**
```
╭─ Index Numerorum Demo ───────────────────────────────────────────────────────╮
│ Creating 20 sample products, embedding, and finding neighbors...             │
╰──────────────────────────────────────────────────────────────────────────────╯
⠋ Loading model & embedding...
╭─ Demo Complete ──────────────────────────────────────────────────────────────╮
│                                                                              │
│  Files created in [cyan]demo_output/[/cyan]:                                  │
│                                                                              │
│  [green]✓[/green] products.xlsx           Source data (20 products)          │
│  [green]✓[/green] products_embedded.xlsx  Data + embedding vectors           │
│  [green]✓[/green] products_neighbors.xlsx Nearest neighbor results           │
│                                                                              │
│  [dim]Open any file in Excel to explore. Try with your own data:[/dim]       │
│  [cyan]index-numerorum embed your_file.xlsx -c "Column Name"[/cyan]          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 2.9 `doctor` Command Output

Add a color banner header:

```
         Index Numerorum — System Doctor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Check                  Status
 ─────────────────────  ─────────────────────────
 ✓ Python version       3.12.3
 ✓ PyTorch              2.10.0+cu128 (cpu)
 ✓ sentence-transformers 5.2.3
 ✓ HF cache             46.5 GB used / 936.8 GB total

 index-numerorum v0.1.0 | Default model: mini | Default metric: cosine
```

---

## 3. Implementation Changes

### Files to modify:

| File | Changes |
|------|---------|
| `cli.py` | Command help text, output formatting for all 7 commands |
| `cli.py` | Epilog examples properly formatted |
| `cli.py` | Timing with `time.time()` for neighbors/compare |
| `cli.py` | Summary panels for embed, compose-key, demo |

### Key patterns to use:

1. **Info panel before work:** `Panel(..., title="...", border_style="blue")`  
2. **Success panel after work:** `Panel(..., title="Complete", border_style="green")`
3. **Error panel:** `Panel(..., title="Error", border_style="red")` (already done)
4. **Timing:** `import time; start = time.time(); elapsed = time.time() - start`
5. **Bar visual:** Helper function `_score_bar(score, metric)` that returns a colored bar string
6. **Command descriptions:** `@app.command(help="...")` parameter

### Helper functions to add:

```python
def _score_bar(score: float, metric: str, width: int = 20) -> str:
    """Generate a visual bar for similarity/distance scores."""
    if metric == "cosine":
        filled = int(max(0, min(width, (score + 1) / 2 * width)))
        return "[green]" + "█" * filled + "[/green]" + "░" * (width - filled)
    if metric in ("euclidean", "manhattan"):
        return ""
    if metric == "dot":
        return ""
    return ""

def _format_elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.1f}s"
```

---

## 4. Test Updates

Add tests for:
- `_score_bar` returns correct bar for cosine
- `_format_elapsed` formats ms and s correctly
- All `--help` outputs contain command descriptions
- Error panels contain "Error" in output (not tracebacks)

---

## 5. Acceptance Criteria

The terminal is "really nice" when:

- [ ] Every `--help` shows one-line command descriptions
- [ ] Every `--help` examples section is visually distinct from options
- [ ] `embed` shows a blue info panel before and green summary after
- [ ] `neighbors` shows timing and clean score bars in separate column
- [ ] `compare` shows names in a panel, highlighted metric is visually distinct
- [ ] `compose-key` shows what key was built (sample value)
- [ ] `models` includes brief model descriptions
- [ ] `demo` shows a unified progress flow and rich completion panel
- [ ] `doctor` has a clean header
- [ ] No raw text output — everything is in panels, tables, or spinners
- [ ] Timing shown for any command that takes > 100ms
- [ ] All 70+ tests still pass
