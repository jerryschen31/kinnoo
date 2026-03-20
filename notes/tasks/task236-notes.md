# Task236 - feature43 tenant model and slug management

## Summary
- Implemented tenant domain model in `server/models/tenant.py`:
  - immutable `Tenant` dataclass with fields `tenant_slug`, `owner_user_id`, `visibility`, `created_at`
  - slug validation rule: lowercase alphanumeric plus hyphens, must start with a letter
  - visibility validation (`public`/`private`)
  - JSON conversion helpers (`to_document`, `from_document`)
- Implemented JSON-backed tenant persistence in `server/storage/tenant_store.py`:
  - one-document-per-tenant storage under `tenants/*.json`
  - uniqueness check for `tenant_slug`
  - admin-only authorization check for tenant creation (`PermissionError` with 403 wording)
  - retrieval/list helpers for future task composition
- Added associated test334 in `server/tests/test_tenant_model.py`:
  - `test_tenant_slug_management` validates:
    - valid tenant creation,
    - duplicate slug rejection,
    - invalid slug rejection,
    - non-admin creation rejection.

## Tests and results
- `python3 -m pytest server/tests/test_tenant_model.py::test_tenant_slug_management` -> `1 passed`

## Bug/error notes
- No bug/error class required iterative fixes for task236.
- Same bug/error class fix attempts: `0` (cap: `5`).

## Teaching notes
- Keep business-rule validation (slug/visibility format) in the model and policy-rule enforcement (admin-only creation) in the store/service layer to avoid coupling domain parsing with authorization.
- For slug uniqueness in file-backed stores, a deterministic filename mapping (`<slug>.json`) provides simple and fast existence checks while remaining easy to migrate to key-value/object stores later.
- Permission errors should encode actionable context early (for example 403 semantics in message text) so API wrappers can preserve intent without brittle string rewrites.
- Unit tests for auth-adjacent models should assert both success paths and refusal paths in the same test when the task contract is scenario-based (as in test334).
