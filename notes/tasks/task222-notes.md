# Task222 - feature40 unsigned archive warning and confirmation path

## Summary
- Updated [src/kinnoo/cli.py](src/kinnoo/cli.py):
	- added install flag `--allow-unverified-publisher` for explicit non-interactive unsigned-publisher override.
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
	- added unsigned-publisher detection when checksum exists but signature artifacts are absent,
	- emits deterministic warning label: `UNVERIFIED PUBLISHER`,
	- requires interactive confirmation in prompted mode,
	- enforces non-interactive safety: `--yes` requires `--allow-unverified-publisher` in unsigned-publisher path,
	- preserves existing unverified-source checksum-missing behavior to avoid unrelated regressions.
- Updated [tests/test_cli_install.py](tests/test_cli_install.py):
	- added mapped test320 `test_feature40_unsigned_archive_warning_and_confirmation`,
	- validates warning visibility,
	- validates interactive deny abort path,
	- validates non-interactive explicit override continuation path.
- Updated [README.md](README.md):
	- documented unsigned-publisher warning prompt and non-interactive override behavior.
- Updated [TASKS.txt](TASKS.txt):
	- `task222` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_install.py::test_feature40_unsigned_archive_warning_and_confirmation` -> `1 passed`

## Bug/error notes
- No implementation bugs encountered after integration.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Keep trust signals layered: checksum verifies integrity, while signatures verify publisher authenticity. Distinguishing these paths produces clearer operator decisions.
- Non-interactive policy should require explicit overrides for risky states; that prevents accidental automation drift into unsafe defaults.
- Feature rollouts in mature CLIs are safer when new policy gates are scoped to precise conditions (here: checksum-present but signature-absent) to reduce compatibility breakage.
