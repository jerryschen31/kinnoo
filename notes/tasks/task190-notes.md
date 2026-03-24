# Task190 - feature34 generated OpenClaw manifest validation contract

## Summary
- Added OpenClaw-specific manifest template in [src/kinnoo/templates.py](src/kinnoo/templates.py):
  - `OPENCLAW_KINNOO_YAML_TEMPLATE` now emits Node daemon + feature33-aligned fields.
- Updated init manifest selection in [src/kinnoo/init_command.py](src/kinnoo/init_command.py):
  - OpenClaw path now uses `OPENCLAW_KINNOO_YAML_TEMPLATE` directly,
  - non-OpenClaw frameworks keep existing baseline + framework/model append behavior.
- Updated CLI framework choices in [src/kinnoo/cli.py](src/kinnoo/cli.py):
  - added `openclaw` to `kinnoo init --framework` accepted values and help text.
- Added task-linked integration test in [tests/test_init.py](tests/test_init.py):
  - `test_feature34_openclaw_manifest_validation_contract` (test288),
  - validates generated OpenClaw manifest with validator,
  - asserts framework/runtime/package-manager/channel contract fields.
- Updated [TASKS.txt](TASKS.txt):
  - `task190` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_init.py::test_feature34_openclaw_manifest_validation_contract` -> `1 passed`

## Bug/error notes
- Bug class 1: framework parsing rejected `openclaw` at CLI layer.
  - Cause: parser choices in `src/kinnoo/cli.py` did not include `openclaw`.
  - Fix: added `openclaw` to choices/help text.
  - Attempts for this bug class: `1`.
- Bug class 2: CLI parser corruption introduced by earlier patch-correction drift.
  - Symptoms: `IndentationError` and then `TypeError` from malformed `install` parser call.
  - Fix: repaired parser block and restored missing positional subcommand name.
  - Attempts for this bug class: `2`.

## Teaching notes
- In CLI tools, framework support has three layers that must stay in sync:
  1. parser choices,
  2. init/template routing,
  3. validator contract.
  Missing any one layer can create false-negative failures even when the template logic is correct.
- For contract-driven manifests, a dedicated template per specialized framework can be safer than incrementally appending fields, because it prevents accidental inheritance of incompatible defaults.
- Task-scoped tests should assert both semantic validation (`validate(...)`) and explicit manifest field values to catch regressions in behavior and generated content shape.
