# Task221 - feature40 install signature verification gate

## Summary
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
	- added install-time detection of signed archive artifacts (`.sig` + `.sig.json`),
	- enforced signed-artifact completeness gate (both files must be present),
	- added signature verification before extraction side effects,
	- added deterministic block-path diagnostics and remediation guidance for invalid signatures.
- Updated [src/kinnoo/signing.py](src/kinnoo/signing.py):
	- added PEM-string public-key loader helper,
	- added detached signature verification helper that validates metadata shape and binding:
		- algorithm
		- archive filename
		- signature filename
		- archive SHA256
		- metadata signature_base64 alignment with `.sig` bytes
		- cryptographic Ed25519 signature verification against archive payload
- Updated [tests/test_install.py](tests/test_install.py):
	- added mapped test319 `test_feature40_install_signature_verification_gate`,
	- validates valid signed archive installs successfully,
	- validates invalid signed archive path is blocked with deterministic verification-failure guidance.
- Updated [TASKS.txt](TASKS.txt):
	- `task221` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_install.py::test_feature40_install_signature_verification_gate` -> `1 passed`

## Bug/error notes
- No implementation bugs remained after integration.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Signature verification should happen before extraction and dependency installation to prevent side effects from unauthenticated artifacts.
- Treat metadata as part of the trust chain: verify not only cryptographic signature validity, but also metadata-to-artifact consistency (filenames, checksums, and detached signature bytes).
- Keeping verification failure diagnostics deterministic and actionable improves operator response and enables stable regression assertions.
