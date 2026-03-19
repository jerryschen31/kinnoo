# Task194 - feature35 state_dirs schema contract and validation rules

## Summary
- Extended feature35 state directory contract validation in [src/kinnoo/validator.py](src/kinnoo/validator.py):
  - added `_collect_state_dirs_contract_errors(...)` for `state_dirs` entries,
  - preserved backward-compatible `state_dirs` string path entries,
  - added structured entry support: `{"path": "...", "exclude": ["..."]}`,
  - enforced safety checks for root paths and exclude patterns (relative-only, no traversal),
  - validated `exclude` shape and item types.
- Added `test292` coverage in [tests/test_validator.py](tests/test_validator.py):
  - `test_feature35_state_dirs_validation_contract`,
  - asserts valid mixed contract passes,
  - asserts deterministic failures for absolute/traversal paths, malformed dict shape, invalid exclude type, unsafe exclude pattern, and invalid exclude item types.
- Updated [TASKS.txt](TASKS.txt):
  - `task194` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py::test_feature35_state_dirs_validation_contract` -> `1 passed`

## Bug/error notes
- No implementation bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- For evolving manifest contracts, design validators to be additive: keep legacy shape support while introducing richer structured entries so existing manifests remain valid.
- Path safety should be enforced at contract boundaries early; allowing absolute or traversal paths in metadata can later become archive extraction or overwrite vulnerabilities.
- Keep diagnostics field-specific and indexed (for example `state_dirs[5].exclude[0]`) so users can quickly correct invalid manifests without trial-and-error.
