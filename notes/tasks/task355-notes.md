# task355 notes

## Summary
- Added `--frozen` install flag in CLI and propagated `frozen_mode` into install command flow.
- Implemented frozen lockfile enforcement checks before extraction:
  - lockfile must exist,
  - agent entry must exist,
  - locked version must match archive manifest version,
  - locked checksum must match archive checksum.
- Added deterministic drift remediation diagnostics: re-run install without `--frozen` to regenerate lockfile.
- Updated install success finalization so frozen-mode installs do not mutate lockfile state.
- Added regression test `test_feature72_frozen_install_and_docs` in `tests/test_cli_install.py`.
- Added README lockfile lifecycle guidance for frozen mode and drift remediation.

## Teaching Notes
- Frozen mode is strongest when validation happens before extraction and dependency side effects.
- For reproducibility workflows, lockfile drift failures should include a single canonical remediation command.
- Treating frozen installs as read-only for lockfile state avoids accidental lock churn in CI.

## Validation
- `python3 -m pytest tests --testmon -k test_feature72_frozen_install_and_docs`
