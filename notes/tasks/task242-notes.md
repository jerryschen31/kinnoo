# Task242 - feature29 list and detail endpoints

## Summary
- Added `server/routes/agents.py` with two framework-agnostic handlers and one router factory:
  - `list_agents_payload(...)` for `GET /api/agents` pagination and optional tenant filter.
  - `agent_detail_payload(...)` for `GET /api/agents/{tenant}/{agent}` detail retrieval.
  - `create_agents_router(...)` for FastAPI route binding.
- Enforced `registry:read` auth scope for both endpoints.
- Implemented visibility guard:
  - `public` entries are readable by any authenticated token.
  - `private` entries are readable only when token `tenant_slug` matches requested tenant (V1 collaborator behavior via tenant-scoped token).
- Added response/error behavior required by task/test contract:
  - pagination support (`offset`, `limit`), optional tenant filter (`tenant`),
  - `404` for non-existent agent detail,
  - `403` for unauthorized private-tenant detail,
  - `401` for missing auth.
- Wired agents routes into app startup in `server/app.py`.
- Added mapped integration test340 at `server/tests/test_agents_routes.py::test_list_and_detail` covering list, paging, filter, detail, visibility, and auth/error paths.

## Tests and results
- `python3 -m pytest server/tests/test_agents_routes.py::test_list_and_detail` -> `1 passed`

## Bug/error notes
- No implementation bug class exceeded retry threshold.

## Teaching notes
- Keep route business logic in pure functions returning `(status, payload)` so behavior can be tested independently of framework adapters.
- For multi-tenant visibility in early versions, use a simple explicit policy boundary first (tenant-scoped token for private data), then layer richer collaborator authorization later without changing endpoint shape.
- Pagination correctness should validate both the `items` slice and the `total` count from the same filtered set; this prevents common UI bugs where page counts and rows disagree.
