# Task327 Notes

## Scope completed
- Added shared relational auth schema artifacts:
  - `server/storage/sql/schema_auth.sql`
  - `server/storage/sql/migrations/001_auth_schema.sql`
- Added auth-store protocol contract in `server/storage/auth_store.py` for SQLite-now/PostgreSQL-later alignment.
- Updated `SQLiteAuthStore` to initialize from shared schema SQL and to persist consumed token state in `one_time_tokens`.
- Added schema/index integration regression for feature60 test485.

## Tests added and coverage
- `tests/test_registry.py::test_feature60_sqlite_auth_schema_and_indexes`
  - Verifies migration creates required tables (`users`, `tenants`, `identities`, `sessions`, `one_time_tokens`).
  - Verifies uniqueness constraints for `tenants.tenant_slug` and `identities(provider, provider_user_id)`.

## Targeted regression command and result
Command:
```bash
cd /Users/jerry/gh/kinnoo && python3 -m pytest tests --testmon -k "test_feature60_sqlite_auth_schema_and_indexes"
```

Result:
```text
1 passed
445 deselected
```

## Teaching notes
- Keeping schema SQL in dedicated files and having runtime code consume those files prevents schema drift between tests, local runtime, and future migrations.
- A protocol module (`AuthStore`) gives a clean seam for switching from SQLite to PostgreSQL without changing route/service call sites.
- Integration tests for uniqueness constraints are especially important for auth boundaries because collisions can create identity-assignment bugs that unit tests often miss.
