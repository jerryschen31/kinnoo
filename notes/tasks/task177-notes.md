# Task177 - feature42 docs preflight inspect and regression gates

## Summary
- Implemented operator-facing Feature42 JSON contract guidance across runtime and docs surfaces:
	- Updated `kinnoo run --help` examples in `src/kinnoo/cli.py` to include `--json-input` and `--json-file` usage.
	- Added explicit preflight I/O contract reporting in `src/kinnoo/run_command.py`:
		- prints declared `inputs.type` and `outputs.type`,
		- explains JSON input mode usage when `inputs.type` includes `json`,
		- explains JSON stdout contract when `outputs.type` includes `json` for one-shot runtimes.
	- Extended inspect metadata output in `src/kinnoo/inspect_command.py` to show:
		- `Input Types`,
		- `Output Types`,
		- `JSON Contract` guidance when applicable.
- Updated documentation for Feature42 in:
	- `README.md`
	- `docs/manifest-schema-reference.md`
- Added/updated tests:
	- `tests/test_docs.py::test_feature42_docs_cover_json_contract_guidance`
	- `tests/test_regression_v1.py::test_feature42_json_contract_guidance_and_text_regression_gate` (test275)
	- `tests/test_cli.py::test_run_usage_includes_feature20_modes` now asserts JSON usage lines.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature42_json_contract_guidance_and_text_regression_gate` -> `1 passed`

## Bug/error notes
- Encountered one bug during execution:
	- `NameError: runtime_type is not defined` in preflight I/O contract rendering path.
- Fix:
	- Added runtime type derivation in preflight from `runtime.type` with `one-shot` fallback before contract rendering.
- Same bug/error class fix attempts: `1` (below the requested stop threshold of 5).

## Teaching notes
- Contract visibility as an operator UX principle:
	- Enforcing contracts is necessary but not sufficient; surfacing those contracts in `--help`, `inspect`, and `--preflight` reduces failure-at-runtime surprises and shortens onboarding/debug cycles.
- Additive compatibility pattern:
	- Feature work can remain low-risk by adding typed pathways (`json`) while explicitly preserving legacy pathways (`text`) and proving that with regression gates.
- Regression-gate composition:
	- A strong gate can combine static guidance checks (docs/help text) with behavioral checks (python and node text flows) so you validate both communication and runtime semantics in one task-linked test.
