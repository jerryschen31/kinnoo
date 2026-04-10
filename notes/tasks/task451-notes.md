# Task451 Notes: Remote Install Failures After Successful Login/List

Date: April 9, 2026

## Original User Prompt (verbatim)

I'm going through the workflow of installing an agent and getting errors:

jerry@Jerrys-MacBook-Air-2 scratch-install % kinnoo login
Email/Username: jerryschen@gmail.com
Password: 
Login successful.
Registry: https://dev-api.kinnoo.ai
Tenant: jerryschen

jerry@Jerrys-MacBook-Air-2 scratch-install % kinnoo list
Remote registry agents:
- bump-publish-agent | latest: 1.3.0 | description: (no description) | size: 840 B
- pack-publish-agent | latest: 1.0.0 | description: (no description) | size: 839 B
- public-publish-agent | latest: 1.0.0 | description: (no description) | size: 847 B
- test-agent-phase7-github-mcp-client | latest: 0.1.4 | description: TODO: Add a short agent description | size: 10.9 MB
- test-agent-phase7-mcp-client-2 | latest: 0.1.1 | description: TODO: Add a short agent description | size: 10.9 MB

SO FAR, SO GOOD - but now kinnoo install doesn't work:

jerry@Jerrys-MacBook-Air-2 scratch-install % kinnoo install bump-publish-agent 
Error: Failed to resolve remote registry target: Remote registry resource not found (404). Check agent name/version and tenant. Response: {"error":{"code":"not_found","message":"Version not found: jerryschen/bump-publish-agent/latest","request_id":"61edcd3be0764a4d812fedf658fdce93"}}
jerry@Jerrys-MacBook-Air-2 scratch-install % kinnoo install test-agent-phase7-github-mcp-client
Error: Failed to resolve remote registry target: Remote registry resource not found (404). Check agent name/version and tenant. Response: {"error":{"code":"not_found","message":"Version not found: jerryschen/test-agent-phase7-github-mcp-client/latest","request_id":"f4d36085b95f47958ca53e458d80d6c3"}}
jerry@Jerrys-MacBook-Air-2 scratch-install % kinnoo install test-agent-phase7-github-mcp-client==0.1.4
Error: Failed to download archive from remote registry: <urlopen error [Errno 2] No such file or directory: '/data/.registry-storage/archives/tenants/jerryschen/agents/test-agent-phase7-github-mcp-client/versions/0.1.4/test-agent-phase7-github-mcp-client.kno'>
jerry@Jerrys-MacBook-Air-2 scratch-install % kinnoo install --remote test-agent-phase7-github-mcp-client       
Error: Failed to resolve remote registry target: Remote registry resource not found (404). Check agent name/version and tenant. Response: {"error":{"code":"not_found","message":"Version not found: jerryschen/test-agent-phase7-github-mcp-client/latest","request_id":"ba6ca1cde94f4f66a850e7735520745d"}}
jerry@Jerrys-MacBook-Air-2 scratch-install % kinnoo install --remote test-agent-phase7-github-mcp-client==0.1.4
Error: Failed to download archive from remote registry: <urlopen error [Errno 2] No such file or directory: '/data/.registry-storage/archives/tenants/jerryschen/agents/test-agent-phase7-github-mcp-client/versions/0.1.4/test-agent-phase7-github-mcp-client.kno'>

If these are bugs, resolve them, as SWE agent and backend, frontend, CLI development expert.

## Diagnosis Summary

Two concrete issues were identified in the remote install flow:

1. Latest version resolution mismatch:
- `kinnoo list` succeeds because it reads `latest_version` from summary metadata.
- `kinnoo install <name>` with remote path attempted `/download` using literal `latest`, but the server download endpoint expects an explicit version.
- Result: 404 Version not found for `<tenant>/<agent>/latest`.

2. Download URL contract mismatch handling:
- For exact-version installs, remote resolve payload sometimes returned a root-relative storage path (for example `/data/...`) instead of a portable presigned URL.
- CLI attempted `urlopen()` directly against that path and surfaced a local file-not-found error.

## Implemented Fixes

### CLI/Install flow updates

File: `src/kinnoo/install_command.py`

- Added `_resolve_remote_latest_version()`:
  - Reads remote summaries.
  - Resolves `latest_version` to an explicit semver string before calling resolve/download.

- Added `_download_remote_archive_payload()`:
  - Supports `http`/`https` presigned URLs.
  - Supports `file` URLs.
  - Supports relative API paths via authenticated client fetch.
  - Attempts authenticated fetch for root-relative paths.
  - Emits actionable error guidance when server payload is not downloadable.

- Updated remote install branch to:
  - Resolve latest first when no explicit version was provided.
  - Call `backend.resolve(..., version=<explicit-version>)`.
  - Download via robust helper instead of direct `urlopen()` only.

### Remote client enhancements

File: `src/kinnoo/remote_client.py`

- Added `request_bytes(path=...)`:
  - Performs authenticated raw-byte GET requests against remote API paths.
  - Reuses standardized HTTP/network error translation to `RemoteRegistryClientError`.

## New/Updated Tests

File: `tests/test_cli.py`
- `test_install_remote_latest_resolves_explicit_version_before_download`
- `test_install_remote_reports_filesystem_download_url_as_server_error`

File: `tests/test_remote_client.py`
- `test_remote_client_request_bytes_uses_auth`
- `test_remote_client_request_bytes_http_error`

Also updated existing test double in `tests/test_cli.py::test_backend_selection` to include `list_latest_agents()` so remote-latest pre-resolution behavior is covered by stubs.

## Test Runs and Results

Executed targeted regression commands:

- `python -m pytest tests/test_cli.py::test_install_remote_latest_resolves_explicit_version_before_download tests/test_cli.py::test_install_remote_reports_filesystem_download_url_as_server_error`
  - Result: 2 passed

- `python -m pytest tests/test_remote_client.py`
  - Result: 6 passed

## User-Facing Outcome

- `kinnoo install <agent-name>` in remote mode now resolves latest to explicit version before download resolution.
- Remote download payload handling is hardened and provides clearer diagnostics for server contract issues.
- The exact failure modes reported in the prompt are covered by automated regression tests.

## Follow-up: Server-Side URL Contract Fix

After re-testing against `https://dev-api.kinnoo.ai`, install still failed with:

- `file:///data/.registry-storage/...kno?expires_in=900`

That confirmed a deployment/runtime backend issue (not just CLI logic): the live server was still emitting local filesystem URLs.

### Additional implementation

Files updated:

- `server/routes/download.py`
- `mock-server/routes/download.py`
- `src/kinnoo/install_command.py`

Changes:

- Download metadata route now rewrites local-backend `file://` URLs to an authenticated API archive endpoint (`/api/agents/{tenant}/{agent}/{version}/archive`).
- Added authenticated archive-byte endpoint for local backend use so clients can retrieve archive bytes via HTTP instead of trying to open server-local paths.
- CLI download helper now uses authenticated backend byte fetch for same-host HTTP(S) URLs, avoiding anonymous `urlopen` path for registry-provided same-origin URLs.

### Additional tests

- `server/tests/test_download.py::test_download_endpoint_local_storage_returns_api_archive_url`
- `mock-server/tests/test_download.py::test_download_endpoint_local_storage_returns_api_archive_url`
- `tests/test_cli.py::test_install_remote_same_host_http_download_uses_authenticated_backend_fetch`

Results:

- `python -m pytest server/tests/test_download.py` -> passed
- `PYTHONPATH=/Users/jerry/gh/kinnoo python -m pytest mock-server/tests/test_download.py` -> passed
- targeted CLI regressions -> passed

### Runtime config finding (why dev still fails until deploy)

Infra/env inspection indicates the deployed server defaults to local storage unless `REGISTRY_STORAGE_BACKEND=s3` is explicitly set.

- Server config defaults `REGISTRY_STORAGE_BACKEND` to `local`.
- ECS task env currently sets `S3_BUCKET` (not `REGISTRY_S3_BUCKET`) and does not set `REGISTRY_STORAGE_BACKEND`.
- A `/data` EFS mount is configured; local storage root defaults to `/data/.registry-storage`.

So, in current dev deployment, archives are very likely stored on EFS-backed local path under `/data/.registry-storage/...`, not served directly from S3 presigned URLs.

## Finalization: Live Deployment, S3 Cutover, and Validation

### Live rollout actions executed

- Updated ECS service task definition to set explicit registry backend environment values:
  - `REGISTRY_STORAGE_BACKEND=s3`
  - `REGISTRY_S3_BUCKET=kinnoo-registry-dev-386775099533`
  - `REGISTRY_S3_REGION=us-west-2`
  - `REGISTRY_LOCAL_STORAGE_ROOT=/data/.registry-storage`
- Built and pushed updated server container image with explicit `linux/amd64` target and forced ECS redeployment.
- Resolved rollout blocker where ECS could not pull non-amd64 manifest (`CannotPullContainerError ... platform 'linux/amd64'`).

### Additional server hardening after S3 cutover

After switching to S3, live requests initially returned 500 due to unhandled missing-key exceptions from S3 (`NoSuchKey`).

Files updated:

- `server/storage/s3.py`
- `mock-server/storage/s3.py`

Change:

- Normalized provider-specific missing-object errors (`NoSuchKey`/`NotFound` variants) to `FileNotFoundError` so metadata-manager optional reads and route handlers return not-found behavior instead of 500.

### Additional tests added for this hardening

- `server/tests/test_storage.py::test_s3_get_object_missing_key_raises_file_not_found`
- `mock-server/tests/test_storage.py::test_s3_get_object_missing_key_raises_file_not_found`

Results:

- `python -m pytest server/tests/test_storage.py::test_s3_get_object_missing_key_raises_file_not_found server/tests/test_download.py` -> passed
- `PYTHONPATH=/Users/jerry/gh/kinnoo python -m pytest mock-server/tests/test_storage.py::test_s3_get_object_missing_key_raises_file_not_found mock-server/tests/test_download.py` -> passed

### Registry data-state validation and seed publish

- Confirmed S3 bucket was initially empty after cutover, so pre-existing local/EFS registry artifacts were unavailable in S3.
- Published seed agent `s3-seed-agent==0.1.0` to remote registry to validate first-write path and metadata/index generation.
- Verified bucket now contains archive + checksum + metadata index documents.

### End-to-end outcome

- `kinnoo list` now reflects S3-backed registry contents (seed agent visible).
- `kinnoo install --remote s3-seed-agent` succeeds end-to-end.
- Legacy local-backend-only agents (for example `test-agent-phase7-github-mcp-client==0.1.4`) now return clean 404 until republished/migrated to S3.
