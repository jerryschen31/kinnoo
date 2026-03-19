# Task205 - feature37 critical vulnerability gate with override

## Summary
- Updated [src/kinnoo/cli.py](src/kinnoo/cli.py) install command to support `--allow-vulnerable` with security-risk help text.
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
  - Node audit summary now returns parsed severity counts.
  - Added default install blocking when Node audit reports one or more critical vulnerabilities.
  - Added explicit override path via `allow_vulnerable=True` to continue with warning visibility.
  - Preserved deterministic severity summary output in both block and override paths.
- Added task-linked test303 in [tests/test_cli_install.py](tests/test_cli_install.py):
  - `test_feature37_critical_gate_default_block_and_allow_override`
  - validates non-override block behavior and override continuation behavior.
- Updated [TASKS.txt](TASKS.txt):
  - `task205` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_install.py::test_feature37_critical_gate_default_block_and_allow_override` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Security policy gates should be explicit and reversible only through intentional operator action; a dedicated flag is clearer than implicit heuristics.
- Keep reporting and policy separate: always print severity summary, then enforce block/allow decisions from parsed counts.
- Preserve deterministic warning text so policy behavior is testable and stable in CI pipelines.
