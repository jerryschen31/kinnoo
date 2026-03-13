# Task119 Notes - Feature18 docs and regression coverage

## Scope implemented
- Added Feature18 documentation to README and schema reference docs.
- Added docs regression test for Feature18 coverage (`test164`).
- Kept doc contract aligned with implemented runtime behavior from tasks 116-118.

## Files changed
- `README.md`
- `docs/manifest-schema-reference.md`
- `tests/test_docs.py`

## Documentation additions
### README.md
- Added section: `Input Safety Guard (Feature18)`.
- Documented:
  - automatic guard execution on `kinnoo run`
  - non-blocking warning/confirm behavior in interactive mode
  - default abort in non-interactive mode for flagged input
  - threat categories: SQL injection, shell command injection, path traversal, SSRF, XSS, template injection
  - `--no-guard` override for CI/automation
  - type-aware checking model
  - Protocol/factory pluggable architecture for future ML guard replacement

### docs/manifest-schema-reference.md
- Added section: `Input Safety Guard reference (Feature18)`.
- Documented guard behavior contract, threat categories, type-aware semantics, and Protocol-based pluggability.

## Test implementation
- Added `tests/test_docs.py::test_feature18_docs_cover_input_safety_guard` (test164).
- Assertions cover required docs strings:
  - `Input Safety Guard`
  - `--no-guard`
  - SQL injection / shell / path traversal / SSRF / XSS / template injection
  - `Protocol`
  - `type-aware`
  - `non-blocking`

## Validation results
- `python3 -m pytest tests/test_docs.py -q` -> `9 passed`
- `python3 -m pytest -q` -> `156 passed, 1 skipped`

## Teaching notes
- In production agent systems, docs-as-contract is crucial for safety controls: behavior must be explicit so operators understand defaults, override semantics, and failure modes.
- Regression tests for docs are valuable when policies matter; they prevent silent drift between implementation and user expectations.
- The `Protocol + factory` documentation point is important for AI engineering interviews: it demonstrates a clean seam for swapping deterministic heuristics with model-based classifiers while preserving integration contracts.
