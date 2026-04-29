# Task126 Notes - Extend init --framework parsing for feature21

## Scope implemented
- Added `pydantic-ai`, `langgraph`, and `openai-agents` to accepted init framework values.
- Preserved existing accepted values (`gemini`, `chatgpt`, `claude-chat`).
- Kept invalid-framework guidance explicit and complete.

## Files changed
- `src/kinnoo/cli.py`
- `src/kinnoo/init_command.py`
- `tests/test_init.py`
- `TASKS.txt`

## Implementation details
- Updated `--framework` choices in the CLI init parser to include all feature21 framework values.
- Updated `SUPPORTED_FRAMEWORKS` in init command validation to match CLI choices exactly.
- Added task126 tests:
  - `test_feature21_framework_invalid_lists_all_choices` (test180)
  - `test_feature21_framework_values_accepted` (test181)

## Bug encountered and fix
- Existing `test_framework_invalid` became stale after framework expansion:
  - It still expected `langgraph` to be invalid.
  - It used a fixed `myagent` path in current working directory, which can collide.
- Fix: changed invalid list to truly invalid values and wrapped each case in a temporary working directory.
- Fix attempts for this bug class: 1 (resolved; below 5-attempt cap).

## Validation and regression results
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`
- `python3 -m pytest tests/test_init.py -k "feature21 or framework"` -> `10 passed, 16 deselected`
- `python3 -m pytest tests/test_init.py` -> `26 passed`

## Teaching notes
- Parser expansion should be tested with both acceptance and discoverability coverage:
  - acceptance verifies valid values parse and dispatch,
  - discoverability verifies invalid values return complete valid-choice guidance.
- Keep framework allow-lists synchronized across all entrypoints. Divergence between argparse choices and secondary validation lists is a common source of user-facing bugs.
- Legacy tests often encode old product assumptions. After adding valid options, revisit negative-path tests first, because they tend to fail for the right reason but with misleading diagnostics.
