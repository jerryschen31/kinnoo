# Task235 - feature43 bootstrap admin CLI command

## Summary
- Implemented one-time bootstrap service in `server/bootstrap.py`:
  - `bootstrap_admin(...)` checks for existing admin users and refuses re-bootstrap when one exists.
  - Generates a secure temporary password.
  - Creates an admin user with `force_password_change=True`.
  - Returns a structured `BootstrapResult` for CLI-safe handling.
- Implemented server CLI bootstrap command in `server/cli.py`:
  - `kinnoo-server bootstrap --store-root <path> [--username <name>]`
  - Prints temporary password once on success.
  - Returns non-zero and clear refusal message when admin already exists.
- Extended user model and store for bootstrap semantics:
  - Added `force_password_change` support in `server/models/user.py`.
  - Added pass-through creation support in `server/storage/user_store.py`.
  - Kept backward compatibility for older user documents by defaulting missing `force_password_change` to `False`.
- Added mapped test333 in `server/tests/test_bootstrap.py`:
  - `test_bootstrap_lifecycle` validates first-run creation, temp-password output, force-password-change flag, and second-run refusal.

## Tests and results
- `python3 -m pytest server/tests/test_bootstrap.py::test_bootstrap_lifecycle` -> `1 passed`

## Bug/error notes
- No bug/error class required iterative fixes for task235.
- Same bug/error class fix attempts: `0` (cap: `5`).

## Teaching notes
- A bootstrap command should return structured results from domain logic (`BootstrapResult`) and leave terminal formatting to the CLI boundary; this keeps security-sensitive logic testable without stdout coupling.
- For one-time initialization flows, enforce idempotency by state-checking at the beginning (`any_admin_exists`) and failing closed with explicit messages.
- Temporary credential generation should use cryptographically secure randomness (`secrets` module) and be emitted once in operator-visible output while avoiding persistent logs.
- Backward-compatible schema evolution (defaulting missing fields when reading older documents) prevents migrations from breaking future auth tasks.
