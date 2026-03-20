# Task234 - feature43 user model and password hashing

## Summary
- Added `server` package scaffolding for remote-registry auth domain:
  - `server/__init__.py`
  - `server/models/__init__.py`
  - `server/storage/__init__.py`
- Implemented user model and secure password utilities in `server/models/user.py`:
  - immutable `User` dataclass with required fields: `id`, `username`, `password_hash`, `role`, `created_at`, `updated_at`
  - `User.create(...)` and JSON roundtrip helpers (`to_document`, `from_document`)
  - password hashing/verification manager with argon2-first support and scrypt fallback
  - verification path avoids plaintext persistence and uses constant-time digest comparison for the fallback algorithm
- Implemented JSON-backed user persistence in `server/storage/user_store.py`:
  - one-document-per-user persistence under `users/*.json`
  - lookup methods (`get_by_id`, `get_by_username`, `list_users`)
  - uniqueness guard on username
  - `any_admin_exists()` helper for upcoming bootstrap task (`task235`)
- Added associated test332 in `server/tests/test_user_model.py`:
  - `test_password_hashing`

## Tests and results
- `python3 -m pytest server/tests/test_user_model.py::test_password_hashing` -> `1 passed`

## Bug/error notes
- No bug/error class required iterative fixes during task234 implementation.
- Same bug/error class fix attempts: `0` (cap: `5`).

## Teaching notes
- For password storage, treat the hash string as the only persisted secret artifact; design model serializers so plaintext password is never represented in object-to-JSON conversion.
- A practical pattern for crypto agility is algorithm negotiation by hash prefix: keep verifier logic backward-compatible (`$argon2...`, `scrypt$...`) so future migrations can be done without forced password resets.
- Constant-time comparison (`hmac.compare_digest`) matters when comparing derived secrets because naive equality checks can leak timing side channels.
- Splitting responsibilities between model (`User`) and persistence (`UserStore`) keeps auth primitives testable and makes it easier to swap storage backends later (filesystem -> S3/DB) without rewriting credential logic.
