# Task175 - feature42 run path JSON input modes

## Summary
- Implemented JSON input delivery modes for `kinnoo run` in [src/kinnoo/cli.py](src/kinnoo/cli.py) and [src/kinnoo/run_command.py](src/kinnoo/run_command.py):
  - Added `--json-input '<json>'` for inline JSON payloads.
  - Added `--json-file <json-file>` for file-based JSON payloads.
- Added deterministic usage/precedence guardrails:
  - `--json-input` and `--json-file` are mutually exclusive.
  - Positional `<input>` cannot be combined with JSON-mode flags.
  - JSON mode is allowed only when manifest `inputs.type` includes `json`.
- Added pre-execution JSON parsing/validation for both modes with actionable diagnostics:
  - Inline parse errors report line/column and parser message.
  - File mode reports missing file and invalid JSON payload details clearly.
- Added normalized payload contract for subprocess execution:
  - Parsed JSON is canonicalized (`sort_keys=True`, compact separators) and passed as the first runtime argument to entrypoint, making inline and file modes behaviorally equivalent.
- Added task-linked integration tests in [tests/test_cli.py](tests/test_cli.py):
  - `test_feature42_run_inline_json_input_mode` (test272)
  - `test_feature42_run_json_file_input_mode` (test273)
- Updated `task175` status in [TASKS.txt](TASKS.txt) to `needs-review`.

## Tests and results
- Scoped task175 regression tests only:
  - `python3 -m pytest tests/test_cli.py::test_feature42_run_inline_json_input_mode tests/test_cli.py::test_feature42_run_json_file_input_mode`
  - Result: `2 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Contract-first CLI design for structured input:
  - Parse/validate at the CLI boundary, not inside agent code. This pushes malformed payload failures earlier and makes error handling consistent across runtimes.
- Canonicalization as a compatibility tool:
  - Converting parsed JSON back into a deterministic serialized form creates a stable subprocess contract while still using simple argv plumbing. This is a pragmatic bridge toward future richer transport channels.
- Mode disambiguation prevents operator mistakes:
  - Explicitly forbidding ambiguous combinations (`<input>` + JSON flags, or both JSON flags together) reduces accidental misuse and keeps command intent unambiguous in automation scripts and CI.
