# Task97 — Document preflight usage and contracts

## Summary
- Updated `README.md` with a dedicated `kinnoo run --preflight` section covering:
	- command usage examples,
	- deterministic checklist semantics,
	- `Ready to run` / `Not ready to run` summary behavior,
	- entrypoint non-execution guarantee,
	- names-only env var security contract.
- Updated `docs/manifest-schema-reference.md` with a Feature14 preflight section documenting:
	- `kinnoo run <agent-dir> --preflight` usage,
	- checklist sections (runtime version, env vars, entrypoint, dependencies),
	- remediation semantics on failure,
	- explicit statement that preflight does not execute entrypoint logic,
	- env var names-only disclosure and no-value logging contract.

## Test125 implementation
- Added `tests/test_docs.py::test_feature14_docs_cover_preflight_contract`.
- Test covers:
	- presence of preflight usage examples,
	- checklist/readiness summary wording,
	- non-execution contract language,
	- names-only / never-print-values security statements.

## Commands and results
- `python3 -m pytest tests/test_docs.py -q` -> `5 passed`
