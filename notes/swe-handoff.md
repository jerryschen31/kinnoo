# SWE Handoff — Pack Safety + Version Automation (task78, task79)

## Scope
Implement two pack-focused items in order:
1. `task78` hotfix: prompt before overwriting an existing `.kno` archive.
2. `task79` enhancement: add `kinnoo pack --bump {patch,minor,major}` and always print packed version on successful pack.

## Recommended Order
- First complete `task78` (overwrite safety prompt) to lock in safe default behavior.
- Then complete `task79` (automated bump + version output line) on top of that flow.

## Required Prompt/Output Contracts
- Overwrite prompt when target exists:
	- `(archive.kno) already exists - are you sure you want to overwrite? (y/n): `
	- Use concrete archive filename in place of `archive.kno`.
- Successful pack output (all success paths, with or without `--bump`):
	- `[kinnoo pack] Agent version: <version #>`

## Tests (exact mapping)
- `task78` → `test105` (`tests/test_pack.py::test_pack_prompts_before_overwrite_existing_archive`)
- `task79` → `test106` (`tests/test_pack.py::test_pack_bump_flag_and_version_output_line`)

## Implementation Notes
- `task78`: `y/Y` proceeds, `n/N` aborts non-zero without archive mutation; treat invalid/empty as safe abort.
- `task79`: when `--bump` is provided, update `kinnoo.yaml` version before pack; bump rules:
	- `patch`: `x.y.z -> x.y.(z+1)`
	- `minor`: `x.y.z -> x.(y+1).0`
	- `major`: `x.y.z -> (x+1).0.0`
- Do not print the version-success line on failed pack attempts.

## Done Criteria
- Both tests pass and task statuses can move to `needs-review`.
- `python3 src/validate_project_manifests.py` passes after any manifest edits.
