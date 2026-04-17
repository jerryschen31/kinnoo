# Task127 Notes - Generate framework templates and metadata artifacts

## Scope implemented
- Added framework-specific template content for `pydantic-ai`, `langgraph`, and `openai-agents`.
- Added major-version range dependency pins for each new framework in generated `requirements.txt`.
- Updated init generation flow to write a `framework` field into generated `kinnoo.yaml` when a framework scaffold is selected.
- Added task127-linked tests `test182` to `test187` in the init test suite.

## Files changed
- `src/kinnoo/templates.py`
- `src/kinnoo/init_command.py`
- `tests/test_init.py`
- `TASKS.txt`

## Implementation details
- New template constants were added for each framework:
  - `run.py` deterministic scaffold text with framework markers
  - pinned `requirements.txt` entries (`>=X.Y,<Z.0` style)
  - README setup sections with framework-specific guidance
- `init_agent()` now:
  - generates `manifest_content` and appends `framework: <value>` for framework scaffolds,
  - uses a framework-to-template map to select run/requirements/README artifacts consistently.

## Tests implemented
- `tests/test_init.py::test_feature21_pydanticai_template_generation` (test182)
- `tests/test_init.py::test_feature21_langgraph_template_generation` (test183)
- `tests/test_init.py::test_feature21_openai_agents_template_generation` (test184)
- `tests/test_init.py::test_feature21_requirements_major_version_pins` (test185)
- `tests/test_init.py::test_feature21_manifests_pass_and_set_framework` (test186)
- `tests/test_init.py::test_feature21_readme_setup_guidance` (test187)

## Validation and regression results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_init.py -k "framework or feature21"` -> `16 passed, 16 deselected`
- `python3 -m pytest tests/test_cli.py -k "feature21"` -> `0 selected` (expected at task127 stage)
- `python3 -m pytest tests/test_regression_v1.py -k "framework or feature21"` -> `0 selected` (expected at task127 stage)

## Issue encountered
- Full-suite command `python3 -m pytest -q` was interrupted by KeyboardInterrupt in this environment before completion (twice).
- This was execution interruption, not a code/test assertion failure.
- Attempts against this interruption class: 2 (below the 5-attempt cap).

## Teaching notes
- For scaffold-heavy work, use a dictionary-based template dispatch rather than long if/elif chains; this reduces branching bugs and makes future framework additions lower-risk.
- Template test strategy should separate concerns:
  - generation presence tests (files and markers),
  - dependency pin format tests,
  - manifest contract tests,
  - documentation guidance tests.
- Add metadata fields at generation time only when needed by mode (`framework` for framework scaffolds), so vanilla defaults remain stable.
- Deterministic templates are excellent for CI reliability; runtime smoke tests can be added later without coupling task127 to live external APIs.
