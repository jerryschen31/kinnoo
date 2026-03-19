# Task212 - feature38 memory snapshot credential scan before pack

## Summary
- Updated [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py):
  - integrated memory snapshot candidate scanning into pack flow using discovered `state_dirs` snapshot files,
  - emits warning-first findings before archive completion,
  - preserves non-blocking pack completion behavior.
- Updated [src/kinnoo/code_sweep.py](src/kinnoo/code_sweep.py):
  - added `sweep_memory_snapshot_credential_risks(...)` helper that reuses safe credential warning contracts without echoing raw values.
- Added task-linked integration test in [tests/test_pack_robustness.py](tests/test_pack_robustness.py):
  - `test_feature38_memory_snapshot_credential_warning_first` (test310),
  - validates warning emission for risky memory snapshot candidate content,
  - validates pack command still succeeds and produces archive output,
  - validates raw credential-like value is not echoed.
- Updated [TASKS.txt](TASKS.txt):
  - `task212` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_pack_robustness.py::test_feature38_memory_snapshot_credential_warning_first` -> `1 passed`

## Bug/error notes
- Initial test fixture used a value format that did not match the existing AWS secret assignment regex; updated fixture to deterministic matching format.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- For security pattern tests, keep fixture strings aligned with production regex contracts to avoid false-negative test failures.
- Warning-first scans should run before artifact creation so operators see risk context without disrupting local iteration workflows.
- Reusing a shared safe-warning formatter across asset and snapshot scans helps maintain no-secret-value invariants consistently.
