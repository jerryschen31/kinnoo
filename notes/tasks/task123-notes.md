# Task123 Notes - Implement run_command flexible input execution flow

## Scope implemented
- Added runtime support for no-input and pass-through modes in `run_command`.
- Enforced manifest-driven no-input policy: run without positional input is allowed only when `inputs.required` is false (or when pass-through args are provided).
- Added pass-through argument forwarding to the agent subprocess in-order.
- Added pass-through guard aggregation via `check_inputs()` and preserved existing prompt/abort semantics.
- Ensured `--no-guard` bypass applies to all input modes.

## Files changed
- `src/kinnoo/run_command.py`
- `tests/test_input_guard_integration.py`
- `tests/test_cli.py`
- `TASKS.txt`

## Implementation details
- Added helper functions in `run_command.py`:
  - `_manifest_inputs_required(...)` for default-true required semantics.
  - `_infer_pass_through_input_type(...)` for lightweight type mapping (`url`, `file_path`, `id`, `string`, default `text`).
  - `_build_pass_through_guard_inputs(...)` to convert pass-through argv into `(param_name, value, input_type)` tuples for guard aggregation.
- Updated runtime gating logic:
  - reject only when all are true: `input_arg is None`, no pass-through args, and `inputs.required` is true.
- Updated guard flow:
  - aggregate warnings from positional input (`check`) and pass-through values (`check_inputs`) when guard enabled.
  - include `(param: <flag>)` suffix in warning lines when param attribution is available.
- Updated subprocess argv assembly:
  - `[python, entrypoint] + [optional positional input] + pass_through_args`.

## Tests implemented
- `tests/test_input_guard_integration.py::test_pass_through_inputs_are_guard_checked` (test173)
- `tests/test_input_guard_integration.py::test_no_guard_bypasses_pass_through_checks` (test174)
- `tests/test_cli.py::test_run_without_input_rejected_when_required` (test175)
- `tests/test_cli.py::test_run_no_input_and_pass_through_modes_both_supported` (test176)

## Bug encountered and resolution
- Encountered fixture-level indentation/YAML formatting defects while adding integration tests (Python `IndentationError`, then malformed YAML in generated manifest).
- Resolved by correcting helper indentation and matching `inputs.required` indentation to the `inputs` map structure.
- Fix attempts for this bug class: 3 (resolved, below the 5-attempt stop threshold).

## Validation and regression results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_validator.py -k "inputs_required" -q` -> `2 passed`
- `python3 -m pytest tests/test_cli.py -k "run" -q` -> `15 passed, 1 deselected`
- `python3 -m pytest tests/test_input_guard_integration.py -q` -> `6 passed`
- `python3 -m pytest tests/test_install.py tests/test_regression_v1.py -q` -> `2 passed`
- `python3 -m pytest -q` -> `168 passed, 1 skipped`

## Teaching notes
- For runtime contracts, parse-layer support and execution-layer support are separate concerns: task122 established transport, task123 completed execution semantics.
- Guard aggregation over pass-through args is a practical “structured safety” pattern: security checks remain centralized while accepting richer runtime input shapes.
- A useful migration strategy in CLI systems is to keep default behavior strict (`required=true`) while introducing explicit opt-in flexibility (`inputs.required: false`), which minimizes accidental behavior drift.
- In agent platforms, param-level warning attribution (`param_name`) improves operator debugging and reduces friction when triaging safety prompts.