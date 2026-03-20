# Task230 - feature28 RemoteRegistryClient HTTP implementation

## Summary
- Added `RemoteRegistryClient` in src/kinnoo/remote_client.py implementing remote registry operations via `urllib.request`.
- Implemented methods required by task230:
  - `publish(...)` -> `POST /api/publish` with multipart form body including archive bytes and metadata
  - `resolve(...)` -> `GET /api/agents/{tenant}/{agent}/{version}/download`
  - `search(...)` -> `GET /api/search?q={query}`
  - `list_agents(...)` -> `GET /api/agents?tenant={tenant}`
- Enforced `Authorization: Bearer <token>` on all HTTP requests.
- Added protocol-compatibility convenience methods (`list_entries`, `list_latest_agents`, `search_agents`) to keep the client shape compatible with existing service integration points before task232 wiring.
- Exported `RemoteRegistryClient` from src/kinnoo/__init__.py.
- Added mapped test328 in tests/test_remote_client.py as `test_remote_client_http_calls` using mocked `urlopen` capture assertions.

## Tests and results
- `python3 -m pytest tests/test_remote_client.py::test_remote_client_http_calls` -> `1 passed`

## Bug/error notes
- No bug/error class required iterative fixes for task230.
- Same bug/error class fix attempts: `0` (cap: `5`).

## Teaching notes
- Building an HTTP client around `urllib.request` keeps dependency surface small and is often enough for deterministic SDK-style clients when you control request/response shape.
- Multipart encoding is easiest to keep reliable by centralizing it in one helper; this avoids duplicated boundary/content-type mistakes across callers.
- Introduce tenant in path construction as a first-class parameter now; it prevents future retrofit bugs when moving from single-tenant assumptions to namespace-aware APIs.
- Writing request-capture tests against `Request` objects is a strong contract test pattern: you validate URL, method, headers, and payload without needing a live server.
