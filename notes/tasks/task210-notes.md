# Task210 - feature38 risky JS execution primitive detection

## Summary
- Updated [src/kinnoo/code_sweep.py](src/kinnoo/code_sweep.py):
  - Added risky JS/TS primitive signatures for `eval(...)`, `new Function(...)`, and child-process execution calls.
  - Restricted risky primitive checks to `.js`, `.mjs`, and `.ts` sources to reduce cross-language false positives.
  - Preserved deterministic warning format with file and line evidence.
- Added task-linked integration coverage in [tests/test_trust_baseline.py](tests/test_trust_baseline.py):
  - `test_feature38_flags_risky_js_execution_primitives_with_file_line` (test308),
  - validates deterministic findings and path/line evidence for eval, Function constructor, and child-process execution patterns.
- Updated [TASKS.txt](TASKS.txt):
  - `task210` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_trust_baseline.py::test_feature38_flags_risky_js_execution_primitives_with_file_line` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Static security checks are most useful when they provide precise location evidence (`file:line`) so remediation effort is low-friction.
- Scope detectors by language where possible to improve signal-to-noise and avoid false positives in unrelated file formats.
- Keep warning messages deterministic and taxonomy-based so they are stable for CI and easy to aggregate in security reporting.
