# Cross-cutting tests split map (Stage 0)

This file records first-pass disposition for tests crossing CLI/web and server boundaries.

## Keep private (server-coupled integration/e2e)

- `tests/client_cli_registry/test_registry.py`
  - Reason: imports `server.*` in-process app/router/middleware/storage internals
  - Follow-up: add `[agent]` comment in future refactor pass for better public/private separation

- `tests/registry_integration/test_web_auth_oidc_logout.py`
  - Reason: imports server web-auth routes/token validation

- `tests/registry_integration/test_oidc_error_handling.py`
  - Reason: imports server auth stack

- `tests/registry_integration/test_lambda_handler.py`
  - Reason: imports root `lambda_handler.py` (private scope)

- `tests/e2e_workflows/test_feature_89.py`
- `tests/e2e_workflows/test_feature_90.py`
- `tests/e2e_workflows/test_feature_91.py`
- `tests/e2e_workflows/test_feature_100.py`
- `tests/e2e_workflows/test_feature_102.py`
  - Reason: server-coupled e2e coverage

## Explicitly deprecate/not migrate to public (per user comment)

- `web/__tests__/wrangler-prod-config.test.ts`
- `tests/e2e_workflows/test_web_frontend_setup.py`

## Keep public

- `tests/registry_integration/test_remote_client.py`
  - Reason: CLI remote-client behavior; no `server.*` import

## Public replacement strategy for private-only integration tests

For each private-only cross-cutting test above, public side should have contract tests using fake HTTP fixtures so CLI/web behavior remains validated without private server imports.
