# task352 notes

## Summary
- Added strict install gate support via a new install CLI flag: --strict.
- Extended install command flow with strict-mode policy checks that fail closed for missing checksum sidecar and missing signature artifacts.
- Enforced strict-mode override safety: --allow-unverified-publisher is explicitly rejected when --strict is enabled.
- Added deterministic strict-mode diagnostics for unsigned archives and invalid signature metadata paths.
- Added regression test test_feature71_strict_install_enforcement in tests/test_cli_install.py.

## Teaching Notes
- Strict mode should evaluate trust prerequisites before side effects (extract/install) so failures are safe and deterministic.
- Fail-closed trust checks are easier to operate when each rejection includes explicit remediation text.
- Security overrides should be mutually exclusive with strict enforcement to avoid policy ambiguity.
- Signature verification and integrity checks are separate controls; strict policy benefits from requiring both.

## Validation
- python3 -m pytest tests --testmon -k test_feature71_strict_install_enforcement
