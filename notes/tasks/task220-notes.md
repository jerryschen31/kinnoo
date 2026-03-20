# Task220 - feature40 pack signing integration

## Summary
- Updated [src/kinnoo/cli.py](src/kinnoo/cli.py):
	- added `kinnoo pack --sign` and `--signing-key` flags,
	- forwarded signing options into pack command execution.
- Updated [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py):
	- extended `pack_agent(...)` signature to include `sign` and `signing_key_path`,
	- enforced deterministic argument contract (`--sign` requires `--signing-key`; key path without `--sign` is rejected),
	- generated detached signature artifacts after archive + checksum generation,
	- kept checksum sidecar behavior unchanged,
	- emitted deterministic signature metadata/output lines and verification hint.
- Updated [src/kinnoo/signing.py](src/kinnoo/signing.py):
	- added `SignatureArtifactResult` model,
	- added archive hashing helper,
	- added `create_detached_signature_artifacts(...)` to produce:
		- `<archive>.kno.sig`
		- `<archive>.kno.sig.json`
	- metadata includes algorithm, archive filename/hash, signature filename/base64, key fingerprint, public key PEM, and verification hint.
- Updated [tests/test_pack.py](tests/test_pack.py):
	- added mapped test318 `test_feature40_pack_sign_emits_signature_and_metadata`,
	- verifies signed pack emits detached signature + metadata artifacts,
	- verifies checksum sidecar remains present for backward compatibility,
	- verifies metadata shape and confirms detached signature validates against generated public key.
- Updated [docs/manifest-schema-reference.md](docs/manifest-schema-reference.md):
	- documented Feature40 signed pack artifacts and metadata contract.
- Updated [TASKS.txt](TASKS.txt):
	- `task220` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_pack.py::test_feature40_pack_sign_emits_signature_and_metadata` -> `1 passed`

## Bug/error notes
- Encountered subprocess import path failure in test318 (`ModuleNotFoundError: No module named 'src'`) for keygen invocation under temporary cwd.
- Fixed by running keygen with the same test environment helper (`_pack_env`) so `PYTHONPATH` includes project root.
- Encountered an indentation parsing error in the new test block.
- Fixed indentation and re-ran mapped test successfully.
- Same bug/error class fix attempts:
	- subprocess import-path issue: `1`
	- indentation/syntax issue: `2`

## Teaching notes
- Detached signatures are best treated as additive artifacts (not replacements) so existing integrity contracts, such as checksum sidecars, remain stable during rollout.
- For test reliability, always align subprocess environment setup across all subprocess calls within a test, especially when using module-style CLI invocation.
- Signature metadata should be explicit and machine-readable; that enables deterministic verification gates in follow-on tasks (install verification and registry trust binding).
