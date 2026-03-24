# Task214 - feature39 permissions schema and validator contract

## Summary
- Updated [src/kinnoo/schema.py](src/kinnoo/schema.py):
	- added feature39 permissions constants for supported keys, boolean fields, and filesystem scope enum values,
	- added optional schema support for `permissions` as a manifest field.
- Updated [src/kinnoo/validator.py](src/kinnoo/validator.py):
	- extended permissions validation to support feature39 fields: `network`, `filesystem_scope`, `shell`, `browser`, `env_access`,
	- added deterministic actionable errors for unsupported keys, invalid enum values, invalid field types, and invalid env_access item shapes,
	- preserved feature26 backward compatibility behavior for non-mcp-server manifests with non-dict legacy permissions payloads.
- Updated [docs/manifest-schema-reference.md](docs/manifest-schema-reference.md):
	- documented feature39 `permissions` schema fields, allowed filesystem scope values, validation behavior, and example payload.
- Updated [tests/test_validator.py](tests/test_validator.py):
	- added mapped test312: `test_feature39_permissions_schema_validation`,
	- validates valid full permissions declaration,
	- validates invalid filesystem scope,
	- validates invalid env_access type,
	- validates unsupported permission key,
	- validates backward compatibility when `permissions` is omitted.
- Updated [TASKS.txt](TASKS.txt):
	- `task214` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_validator.py::test_feature39_permissions_schema_validation` -> `1 passed`

## Bug/error notes
- Initial test insertion accidentally captured the tail of `test_feature26_permissions_schema_validation` inside the new feature39 test body.
- Fixed by restoring correct function boundaries and reran scoped test successfully.
- Same bug/error class fix attempts: `1`.

## Teaching notes
- When extending schema contracts, keep compatibility layers explicit in validator routing (for example, legacy-vs-new keyset handling) to avoid accidental regressions.
- Deterministic validation messages should include the exact field path and accepted values; this improves both UX and test robustness.
- For test additions in large files, re-read the surrounding region immediately after insertion to confirm function boundaries before running tests.
