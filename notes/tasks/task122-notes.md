# Task122 Notes - Update run CLI parsing for no-input and pass-through

## Scope implemented
- Updated `kinnoo run` CLI parsing to support optional positional input plus pass-through capture after `--`.
- Preserved legacy single-input run behavior.
- Preserved existing flag semantics for `--preflight` and `--no-guard` while adding pass-through support.

## Files changed
- `src/kinnoo/cli.py`
- `src/kinnoo/run_command.py`
- `tests/test_cli.py`
- `TASKS.txt`

## Implementation details
- Added pre-parse split logic in `cli.py` for `run` invocations containing `--`:
  - Arguments before `--` are parsed by argparse.
  - Arguments after `--` are captured as `pass_through_args` and forwarded to runtime layer.
- Removed parser-level `argparse.REMAINDER` positional strategy after it regressed option parsing for `--no-guard` placed after input.
- Forwarded `pass_through_args` to `run_agent(...)` from CLI.
- Extended `run_agent(...)` signature with optional `pass_through_args` placeholder (no execution-flow behavior change yet; runtime behavior is task123 scope).

## Tests implemented
- `tests/test_cli.py::test_run_without_input_allowed_when_inputs_not_required` (test170)
- `tests/test_cli.py::test_run_pass_through_args_forwarded_verbatim` (test171)
- `tests/test_cli.py::test_run_single_input_backward_compatible` (test172)

## Validation and regression results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_validator.py -k "inputs_required" -q` -> `2 passed`
- `python3 -m pytest tests/test_cli.py -k "run" -q` -> `13 passed, 1 deselected`
- `python3 -m pytest tests/test_input_guard_integration.py -q` -> `4 passed`
- `python3 -m pytest tests/test_install.py tests/test_regression_v1.py -q` -> `2 passed`
- `python3 -m pytest -q` -> `164 passed, 1 skipped`

## Bug encountered and fix
- Encountered a parser regression where `argparse.REMAINDER` caused `--no-guard` after positional input to be consumed as pass-through data.
- Fix: switched to explicit split-on-`--` preprocessing before argparse parse, restoring stable option parsing while still capturing pass-through args.

## Teaching notes
- CLI grammar changes are safest when modeled as a two-phase parse:
  - shell-level delimiter handling (`--`) first,
  - structured option parsing second.
- Backward compatibility in CLI evolution is mostly about tokenization rules and option precedence, not only business logic.
- For agent systems, adding pass-through transport in one task and runtime semantics in a later task is a good staged-delivery pattern: parser contract first, execution semantics second, security integration third.