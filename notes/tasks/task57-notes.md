## task57 - secret non-disclosure guardrails

- Added runtime guardrail helpers in `src/kinnoo/run_command.py`:
	- `_redact_secrets(text, secret_values)`
	- `_print_safe_error(message, secret_values=None)`
- Updated run command error output paths to use safe error printing and added guarded subprocess launch exception handling with redaction against resolved env var values.
- Added reusable test helper in `tests/test_cli_env_vars.py`:
	- `assert_no_secret_leak(outputs: list[str], sentinels: list[str])`
- Added `test_secret_values_never_appear_in_output_or_logs` (test84), covering env/.env/prompt/cancel paths and asserting sentinel values are absent from captured stdout/stderr.
- Validation run:
	- `python3 -m pytest tests/test_cli_env_vars.py -k "feature10 or env_vars or secret"` -> 7 passed
