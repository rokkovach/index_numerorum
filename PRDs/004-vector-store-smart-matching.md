# PRD 004: Vector Store & Smart Matching

**Date:** 2026-04-17  
**Status:** Executed  
**Depends on:** PRD 001, 002, 003

## What was built

Optional zvec-backed persistent vector store with threshold matching and dedup grouping.

### Commands added

| Command | What it does |
|---------|-------------|
| `store init` | Create store from xlsx, embed, persist |
| `store add` | Incrementally add rows (skips existing keys) |
| `store match` | Find all pairs above similarity threshold + group_id clustering |
| `store annotate` | Write match annotations (_match_ids, _best_match_id, _group_id) back into xlsx |
| `store query` | Free-text search against store |
| `store info` | Show store metadata |

### Enhancements

- `neighbors --threshold` flag filters results by min similarity
- `doctor` checks zvec availability

### Dependency

`pip install index-numerorum[vec]` — optional, graceful fallback if not installed.

### Architecture

- `store.py`: VectorStore class wrapping zvec + sidecar files (_keys.json, _embeddings.npy)
- Union-find clustering for dedup groups via `_compute_groups()`
- COSINE metric in zvec, similarity = 1 - distance

### Critique notes (pre-execution)

- Reduced from 8 commands to 5 (removed delete, cross-match, merged query into annotate)
- Auto-threshold deferred to Phase 2
- delete deferred — users can re-create stores
- cross-match deferred — can be done via annotate with different input

### Post-execution notes

- zvec creates directories itself; calling `mkdir()` before `create_and_open()` causes ValueError
- zvec `query()` takes `topk` as a keyword arg on `collection.query()`, not on `VectorQuery()`
- zvec query returns `Doc` objects (`.id`, `.score`, `.fields`), not dicts
- zvec uses file locks; two read-write handles on the same collection raise RuntimeError
- COSINE metric score is cosine distance (0 = identical); similarity = 1 - score
- Test count went from 82 to 108 (+26 store tests)
- All 5 deferred features remain deferred; no scope creep
