# Task281 Notes - Inspect full/raw views and update flow

Date: 2026-03-23
Status: needs-review

## Scope implemented
- Added inspect rendering flags:
  - `--full`: renders all known manifest metadata fields and prints `N/A` for unset fields.
  - `--raw`: renders metadata as dotted-path key/value output.
  - `--raw --full`: renders all known metadata fields as dotted-path key/value output, including `N/A` placeholders.
- Added inspect update workflow:
  - `kinnoo inspect --update <target> <old-key> <new-value>`
  - Interactive confirmation prompt with default `No`.
  - `--skip-warnings` bypasses interactive confirmation.
  - Updates are validated against manifest schema before writing.
  - Invalid updates are rejected and no file changes are written.

## Files changed
- `src/kinnoo/cli.py`
- `src/kinnoo/inspect_command.py`
- `tests/test_cli_inspect.py`
- `FEATURES.txt`
- `TASKS.txt`
- `TESTS.txt`

## Manifest planning updates
- Added `feature48` with AC1-AC4 for inspect `--full`, `--raw`, combined mode, and update flow.
- Added `task281` mapped to `feature48`.
- Added tests `test414` through `test420` mapped to `feature48` acceptance criteria.

## Test coverage added
- `test_feature48_inspect_full_shows_all_known_fields_with_na`
- `test_feature48_inspect_raw_shows_filled_dotted_fields`
- `test_feature48_inspect_raw_full_shows_all_dotted_fields`
- `test_feature48_inspect_update_prompts_and_applies_on_yes`
- `test_feature48_inspect_update_aborts_on_default_no`
- `test_feature48_inspect_update_skip_warnings_bypasses_prompt`
- `test_feature48_inspect_update_rejects_invalid_manifest_value`

## Test runs
Command:
```bash
python3 -m pytest tests/test_cli_inspect.py -k "feature48"
```
Result:
```text
7 passed, 8 deselected
```

Command:
```bash
python3 -m pytest tests --testmon -k "feature48 and inspect"
```
Result:
```text
7 passed, 398 deselected
```

Command:
```bash
python3 src/validate_project_manifests.py
```
Result:
```text
Validation passed: manifests are consistent
```

## Notes
- The user-provided example `runtime.language javascript` is intentionally rejected because current schema supports `python` and `nodejs` values for `runtime.language`.
- `--update` is restricted to agent directories (not `.kno` archives) since archives are immutable artifacts in this workflow.
