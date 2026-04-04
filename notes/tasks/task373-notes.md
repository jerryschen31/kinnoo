# Task373 Notes

## Summary
Implemented Feature81 task373 by enforcing OpenClaw gateway-aware preflight for `kinnoo run` and adding `--json` output passthrough while preserving text prompt as the default input flow.

## What Was Implemented
- Updated run CLI parser in `src/kinnoo/cli.py`:
  - added `--json` flag for OpenClaw output passthrough
  - passed `openclaw_json_output` into `run_agent(...)`
- Updated OpenClaw run path in `src/kinnoo/run_command.py`:
  - added preflight call `run_openclaw_preflight_for_command("run")`
  - fail-fast deterministic error on preflight failure
  - appends delegated `--json` to OpenClaw command when requested
  - kept text prompt (`input_arg`) as default run input path

## Test Coverage
- Added/validated:
  - `tests/test_cli.py::test_feature81_gateway_preflight_and_json_output_passthrough`
- Verifies:
  - gateway-down preflight fails with deterministic guidance
  - default run path remains text-input driven
  - `--json` output mode passes through machine-readable OpenClaw output
  - delegated command contract includes `--json` only when requested

## Smoke Tests
- `notes/tasks/task373-smoke-tests.md` was not present; no additional smoke steps were executed.

## Teaching Notes
- Why preflight is done before delegation:
  - It prevents executing runtime calls when known prerequisites are absent, reducing noisy failures and partial side effects.
- Why output passthrough is separated from input mode:
  - Keeping input text-default avoids widening operator UX complexity while still enabling machine-readable downstream automation on output.
