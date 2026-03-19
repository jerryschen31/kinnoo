# Task215 - feature39 install-time permission disclosure and consent flow

## Summary
- Updated [src/kinnoo/cli.py](src/kinnoo/cli.py):
	- added install flag `--accept-permissions` for explicit non-interactive permissions consent.
- Updated [src/kinnoo/install_command.py](src/kinnoo/install_command.py):
	- added deterministic install-time permissions summary rendering for `permissions` declarations,
	- added explicit interactive consent prompt with default-safe deny behavior,
	- enforced non-interactive safety: `--yes` installs with declared permissions now require explicit `--accept-permissions` override,
	- retained backward compatibility for manifests without `permissions` declarations.
- Updated [tests/test_cli_install.py](tests/test_cli_install.py):
	- added mapped test313 `test_feature39_install_permission_summary_and_consent`, covering:
		- permission summary visibility,
		- interactive deny abort behavior,
		- interactive accept path,
		- non-interactive failure without override,
		- non-interactive success with `--accept-permissions`.
- Updated [README.md](README.md):
	- documented feature39 install permission disclosure prompts and non-interactive override semantics.
- Updated [TASKS.txt](TASKS.txt):
	- `task215` -> `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_cli_install.py::test_feature39_install_permission_summary_and_consent` -> `1 passed`

## Bug/error notes
- No implementation bugs encountered after initial code integration.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Consent gates should be explicit and layered: summary for visibility, prompt for deliberate approval, and dedicated automation override for CI safety.
- Non-interactive flags should never silently bypass security-sensitive consent checks; requiring a distinct acknowledgement flag keeps operator intent unambiguous.
- In security-adjacent tests, include both positive and negative control paths in one scenario to lock behavior and prevent future accidental bypass regressions.
