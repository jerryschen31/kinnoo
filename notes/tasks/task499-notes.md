# Task499 Notes

## Summary
- Implemented hosted CLI login with PKCE + loopback callback server and dynamic port fallback in `src/kinnoo/auth_command.py`.
- Extended persisted auth state schema in `src/kinnoo/config.py` to include refresh metadata and OIDC endpoints/client references.
- Added refresh-before-use hooks in remote registry command paths (`list`, `search`, `fetch`, `install`, `publish`) using shared refresh helper.
- Added CLI tests covering hosted login state persistence and refresh/logout semantics (`tests/client_cli_registry/test_feature118_cli_auth.py`).

## Teaching Notes
- PKCE is the right default for public/native clients: no client secret on-device, proof-of-possession via code verifier/challenge.
- Dynamic loopback ports improve local reliability and reduce conflicts; callback correctness must include strict `state` verification.
- Refresh logic should fail with actionable re-login guidance rather than silently retrying indefinitely.
