
## 2026-03-06 — SWE Progress Summary (Pack enhancement task79 / test106)

- Implemented `task79` in `src/kinnoo/cli.py` and `src/kinnoo/pack_command.py`.
- Added `kinnoo pack --bump {patch,minor,major}` CLI support.
- Pack now applies bump to `kinnoo.yaml` version before archive creation when `--bump` is provided:
	- `patch`: `x.y.z -> x.y.(z+1)`
	- `minor`: `x.y.z -> x.(y+1).0`
	- `major`: `x.y.z -> (x+1).0.0`
- Added success output contract for all successful pack runs:
	- `[kinnoo pack] Agent version: <version #>`
- Version-success line is emitted only on successful pack completion, not on failed attempts.

### Test coverage (test106)

- Added `tests/test_pack.py::test_pack_bump_flag_and_version_output_line`.
- Test verifies:
	- no-bump pack prints current version line,
	- patch/minor/major bump update manifest version and print updated version line,
	- invalid `--bump` value fails and does not print version-success line.

### Validation results

- `python3 -m pytest tests/test_pack.py::test_pack_bump_flag_and_version_output_line tests/test_pack.py::test_pack_prompts_before_overwrite_existing_archive` → passed (`2 passed`)
- `python3 scripts/validate_project_manifests.py` → Validation passed

### Bookkeeping

- Updated `TASKS.txt`: `task79` status set to `needs-review`.
