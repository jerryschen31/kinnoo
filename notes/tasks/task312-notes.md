# Task312 Notes - Local Admin Bootstrap from Environment

## Summary
- Added new auth service helper in `server/auth/services.py` to ensure/promote an admin account idempotently.
- Added `bootstrap_admin_from_env()` in `server/bootstrap.py` for env-driven bootstrap behavior with secret-safe messages.
- Extended `ServerConfig` in `server/config.py` to include:
  - `registry_admin_email`
  - `registry_admin_password`
- Wired app startup in `server/app.py` to call env-driven bootstrap during initialization.
- Added `test_feature56_admin_bootstrap_secret_safe` in `tests/test_registry.py`.

## Why this implementation
- Keeps admin bootstrapping deterministic for local/dev startup and safe for repeated restarts.
- Centralizes role-promotion/ensure behavior in an auth service helper for reuse and maintainability.

## Teaching Notes
- Idempotent bootstrap code should safely handle repeated runs by design, not by side effects.
- Secret-safe reporting means response messages should communicate outcomes without exposing raw secret values.
- Promoting an existing user to admin can be safer than trying to create duplicates when usernames are unique keys.

## Task-scoped regression
- Command: `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests --testmon -k test_feature56_admin_bootstrap_secret_safe`
- Result: pass (`1 passed`)
