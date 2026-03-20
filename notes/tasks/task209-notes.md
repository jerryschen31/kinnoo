# Task209 - feature38 JS TS JSON credential scanning rules

## Summary
- Updated [src/kinnoo/code_sweep.py](src/kinnoo/code_sweep.py):
  - Expanded sweep file discovery to include `.py`, `.js`, `.mjs`, `.ts`, and `.json` files.
  - Added high-confidence credential/token pattern detectors for common JS/TS/JSON secret forms.
  - Preserved warning-first behavior with redacted reporting style (pattern descriptions only, no raw secret values).
- Added task-linked integration test in [tests/test_trust_baseline.py](tests/test_trust_baseline.py):
  - `test_feature38_scans_jstsjson_credentials` (test307),
  - validates findings are emitted for js/mjs/ts/json fixtures,
  - validates output does not leak raw secret values.
- Updated [TASKS.txt](TASKS.txt):
  - `task209` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_trust_baseline.py::test_feature38_scans_jstsjson_credentials` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Cross-language security sweeps should keep a stable output contract so new detectors do not break downstream tooling.
- High-confidence regex rules should report pattern categories and locations, not raw matches, to reduce accidental secret exposure in logs.
- Add fixture coverage per file type whenever scope expands to prevent silent regressions in discovery logic.
