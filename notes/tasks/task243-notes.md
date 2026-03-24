# Task243 - feature29 download endpoint with presigned URLs

## Summary
- Added `server/routes/download.py` implementing:
  - `download_payload(...)` business logic for auth, metadata lookup, visibility check, and presigned URL generation.
  - `create_download_router(...)` FastAPI binding for `GET /api/agents/{tenant}/{agent}/{version}/download`.
- Endpoint behavior implemented per task contract:
  - requires `registry:read` scope,
  - returns JSON with `download_url` and `expires_in`,
  - returns `404` when version metadata does not exist,
  - does not proxy archive bytes through the API response.
- Wired download router into app startup in `server/app.py` using configured `REGISTRY_PRESIGN_TTL_SECONDS` (`presign_ttl_seconds`).
- Added mapped integration test341 in `server/tests/test_download.py::test_download_presigned` covering:
  - successful presigned URL response,
  - mocked storage presigned URL generation for deterministic contract validation,
  - response includes `download_url` and `expires_in`,
  - non-existent version returns `404`,
  - missing auth returns `401`.

## Tests and results
- `python3 -m pytest server/tests/test_download.py::test_download_presigned` -> `1 passed`

## Bug/error notes
- No bug/error class exceeded retry threshold.

## Teaching notes
- Presigned download APIs should return references (URLs), not binary payloads; this keeps app servers stateless and avoids unnecessary bandwidth/CPU bottlenecks.
- Keep auth/visibility checks in route-adjacent business functions so permission logic is testable without requiring full HTTP stack setup.
- Include TTL (`expires_in`) in response to let clients reason about refresh timing and avoid stale-link failures.
