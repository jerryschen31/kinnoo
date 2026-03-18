# Task176 - feature42 json output contract enforcement

## Summary
- Implemented JSON output contract enforcement for `kinnoo run` in [src/kinnoo/run_command.py](src/kinnoo/run_command.py):
  - Added manifest helper to detect `outputs.type: json` declarations.
  - Added a streamed output capture path for one-shot execution that preserves terminal streaming while capturing stdout/stderr for post-run validation.
  - Added JSON contract validation: when `outputs.type` includes `json` and process exits success, stdout must parse as valid JSON.
  - Added deterministic, actionable failure diagnostics for malformed JSON output including parse line/column without echoing payload values.
- Added integration coverage in [tests/test_cli.py](tests/test_cli.py):
  - `test_feature42_json_output_contract_enforcement` (test274)
  - Covers both valid JSON output success and invalid JSON output deterministic failure semantics.
- Updated `task176` status in [TASKS.txt](TASKS.txt) to `needs-review`.

## Tests and results
- Scoped task176 regression test only:
  - `python3 -m pytest tests/test_cli.py::test_feature42_json_output_contract_enforcement`
  - Result: `1 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Streaming-plus-validation pattern:
  - For contract enforcement on process output, you often need both real-time UX and post-hoc validation. A dual-path approach (stream while buffering) preserves operator experience and still enables strict contract checks.
- Contract checks should be conditional and explicit:
  - Enforce JSON parsing only when the manifest declares `outputs.type: json`; this keeps legacy text workflows backward compatible while making typed contracts meaningful.
- Secret-safe diagnostics principle:
  - Error diagnostics should include structural parse context (line/column/message) but avoid dumping raw payloads. This reduces accidental leakage risk in CI logs and shared run output.
