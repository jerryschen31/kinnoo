## SWE Handoff

### Scope
Implement feature40 from [FEATURES.txt](FEATURES.txt) using tasks task219-task223 from [TASKS.txt](TASKS.txt). This is the archive-authenticity layer and must preserve existing checksum/integrity behavior while adding publisher-verification guarantees.

### Feature Intent
Add Ed25519 key generation, signed archive packaging, signature verification at install, unsigned-publisher warning flows, and registry publisher-key association so users can verify authenticity in addition to archive integrity.

### Task Breakdown (Execution Order)
1. task219: Implement `kinnoo keygen` Ed25519 keypair generation workflow.
2. task220: Integrate `kinnoo pack --sign` signature artifact + metadata emission.
3. task221: Add install-time signature verification gate with invalid-signature block path.
4. task222: Add unsigned archive "UNVERIFIED PUBLISHER" warning and confirmation/override flow.
5. task223: Extend registry metadata model to associate publisher public keys for verified distribution.

### AC Coverage Map
- AC1 -> task219 -> test317
- AC2 -> task220 -> test318
- AC3 -> task221 -> test319
- AC4 -> task222 -> test320
- AC5 -> task223 -> test321

### Key Implementation Constraints
- Maintain backward compatibility for existing checksum outputs and integrity checks from feature16.
- Ensure signature payload canonicalization is deterministic so verification is stable across environments.
- Block invalid signatures by default with clear remediation, and avoid ambiguous warning-only behavior for signed-but-invalid archives.
- Preserve no-secret-value diagnostics: never print private key material or sensitive signature internals in logs.
- Keep signing/verification logic modular (`src/kinnoo/signing.py`) to enable future key-rotation and trust-policy extensions.

### JS/TS Test Guidance
- Feature40 behavior is CLI/package/crypto workflow and should be validated primarily via pytest integration tests.
- Do not add Vitest unless a JS/TS-native signing/verification path is introduced that cannot be reliably exercised from pytest.
- If Vitest becomes absolutely required, ensure TESTS.txt `automation_path` points to a concrete function in a `.js` or `.ts` test file.

### Suggested Files to Touch
- src/kinnoo/cli.py
- src/kinnoo/signing.py
- src/kinnoo/pack_command.py
- src/kinnoo/install_command.py
- src/kinnoo/registry.py
- docs/manifest-schema-reference.md
- README.md
- tests/test_cli.py
- tests/test_pack.py
- tests/test_install.py
- tests/test_cli_install.py
- tests/test_registry.py
- tests/test_cli_registry.py

### Verification Gate
- Run targeted tests for test317-test321.
- Run pack/install/registry regression slices for signed and unsigned archive flows.
- Run full regression before handoff completion:
	- python3 -m pytest
- Validate manifests after task/test updates:
	- python3 src/validate_project_manifests.py

### Status Workflow Guidance
- Move tasks task219-task223 from not-started -> in-progress when implementation begins.
- Move tasks to needs-review after code + tests are complete.
- Do not set completed until Tech Lead review and merge approval.
