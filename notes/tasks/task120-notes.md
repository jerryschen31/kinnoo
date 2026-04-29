# Task120 Notes - Reduce SQL comment false positives while preserving detection rigor

## Scope implemented
- Tuned SQL comment-sequence detection in `RegexInputGuard` to require SQL-like context before flagging comment markers.
- Added focused regression tests for both sides of the precision boundary:
  - benign marker-only text should remain safe,
  - contextual SQL comment-injection payloads should remain detected.

## Files changed
- `src/kinnoo/input_guard.py`
- `tests/test_input_guard.py`

## Guard logic refinement
- Updated SQL comment pattern from a broad optional-prefix match to a contextual match requiring one of:
  - quote context followed by SQL comment marker (`--`, `#`, `/*`), or
  - SQL keyword context (`select`, `union`, `insert`, `update`, `delete`, `drop`, `where`, `from`, `or`, `and`) near a comment marker.
- This reduces false positives for benign prose containing `#` or `--` while preserving attack-signal detection.

## Tests implemented
- `tests/test_input_guard.py::test_sql_comment_markers_benign_text_not_flagged` (test165)
- `tests/test_input_guard.py::test_sql_comment_injection_context_still_detected` (test166)

## Validation results
- `python3 -m pytest -q tests/test_input_guard.py` -> `13 passed`
- `python3 -m pytest -q tests/test_input_guard_integration.py` -> `4 passed`
- `python3 -m pytest -q` -> `158 passed, 1 skipped`
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Teaching notes
- Precision vs recall is a core tradeoff in security classifiers. Regex guards optimize for deterministic recall, but production quality depends on precision tuning to avoid alert fatigue.
- Contextual features improve precision: a token such as `--` is weak alone but becomes strong when paired with SQL syntax context.
- This pattern is directly analogous to AI safety pipelines: lightweight deterministic filters first, then richer context-aware checks. In ML terms, we moved from a unigram-style heuristic to a small context window around indicators.
- Interview framing tip: describe this as threshold calibration in a rule-based detector, backed by paired regression tests that lock in both false-positive and true-positive behavior.
