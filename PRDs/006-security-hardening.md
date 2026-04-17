# PRD 006: Security Hardening

**Date:** 2026-04-17
**Status:** Executed
**Priority:** High

## Problem

Index Numerorum processes sensitive data (company names, addresses, vendor lists) with a promise of zero data egress and local-only processing. A security audit found 16 issues across supply chain, data handling, file safety, and CI/CD.

## Threat Model

| Threat | Vector | Impact |
|--------|--------|--------|
| Supply chain compromise | Unpinned deps pull malicious code | Full system compromise |
| Data leak via xlsx | Embedding vectors in output files | Fingerprintable data exposure |
| Arbitrary code execution | Crafted .npy file with pickle payload | Full system compromise |
| Data corruption | Non-atomic sidecar writes in store | Silent key/embedding misalignment |
| CI compromise | Unpinned GitHub Actions | Repository tampering |
| Accidental data commit | input/output folders not gitignored | Data leak via git push |

## Fixes

### HIGH priority

1. **Pin all dependencies** to exact versions with upper bounds
2. **Strip embedding columns** from all xlsx output in `embed` command
3. **`np.load(allow_pickle=False)`** in store.py

### MEDIUM priority

4. **Redact sensitive values** from error messages in neighbors.py
5. **Add input/, output/, *.npy to .gitignore**
6. **Atomic file writes** in store.py sidecar files
7. **Harden GitHub Actions**: permissions, SHA-pinned actions, no credential persist
8. **Symlink safety check** before rmtree in models --remove

### LOW priority

9. **Disable HF telemetry** via environment variable
10. **Formula injection sanitization** on xlsx write

## Acceptance Criteria

1. No embedding columns in any xlsx output file
2. `np.load` always called with `allow_pickle=False`
3. All dependencies pinned to exact versions
4. GitHub Actions uses minimal permissions and SHA-pinned actions
5. `.gitignore` covers input/, output/, *.npy, *.npz
6. Store sidecar writes are atomic (write-to-tmp + rename)
7. No sensitive data values in error messages
8. HF telemetry disabled by default
9. All 124+ tests pass, lint clean
