# Task166 - feature19 schema-conditional prompts and entrypoint bridge handling

## Summary
- Implemented task166 import flow updates in [src/kinnoo/import_command.py](src/kinnoo/import_command.py):
	- Added confidence-gated prompts for `runtime.type`, `services`, and `permissions` (permissions only for low-confidence `mcp-server` runtime selection).
	- Added service normalization from analyzer output into schema-compatible manifest entries (`name` + `type`, optional HTTP health-check mapping).
	- Added entrypoint compatibility assessment that emits a non-blocking warning when the inferred entrypoint likely does not match kinnoo one-shot CLI contract.
	- Added opt-in wrapper generation path (`kinnoo_wrapper.py`) and manifest entrypoint rewrite when selected by user.
- Added focused task166 tests in [tests/test_cli_import.py](tests/test_cli_import.py):
	- `test_feature19_conditional_prompts_for_runtime_services_permissions` (test259)
	- `test_feature19_entrypoint_warning_and_optional_wrapper` (test260)
- Updated `task166` status to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_import.py::test_feature19_conditional_prompts_for_runtime_services_permissions tests/test_cli_import.py::test_feature19_entrypoint_warning_and_optional_wrapper` -> `2 passed`

## Bug/error notes
- No implementation or test failures encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Prompt minimization scales better when each field has explicit confidence gating; this keeps workflows fast for high-confidence projects while still collecting missing metadata in uncertain cases.
- A warning-first compatibility check is a robust migration strategy: users can continue onboarding without hard failure, then opt into wrapper bridging only when they need it.
- Optional wrappers are a practical adapter pattern for agent migration. They preserve legacy code paths while establishing a predictable execution contract at the platform boundary.