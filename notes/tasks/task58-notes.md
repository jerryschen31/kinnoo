## task58 - docs security contract and operator guidance

- Updated `README.md` with Feature10 `env_vars` security contract:
	- resolution order: process environment -> agent-local `.env` -> masked prompt
	- non-disclosure invariant: secret values must never be printed/logged/persisted
	- safe troubleshooting steps that reference variable names only
- Updated `docs/manifest-schema-reference.md` with Feature10 runtime security contract section, including resolution order and non-disclosure requirements.
- Updated `notes/swe-handoff.md` with a docs checklist for task58 to keep future work aligned.
- Added `test_feature10_docs_cover_env_vars_security_contract` (test85) in `tests/test_docs.py`.
- Validation run:
	- `python3 -m pytest tests/test_docs.py -k "feature10 or feature9"` -> 2 passed
