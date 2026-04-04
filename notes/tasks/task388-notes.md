# Task 388 Notes

## Summary
Implemented task388 for feature89 by hardening server runtime foundations:
- Added production-aware server config fields in server/config.py:
  - KINNOO_ENV (dev|production)
  - CORS_ORIGINS parsing with restrictive production defaults
  - app_version, uvicorn_workers, uvicorn_timeout_seconds
- Added CORS middleware wiring in server/app.py with configured allowed origins.
- Upgraded health endpoint:
  - GET /health now returns {"status": "ok", "version": "..."}
- Added readiness endpoint:
  - GET /ready returns 200 when auth store and storage readiness checks pass
  - returns 503 with detailed checks when not ready
- Added production JSON logging formatter/config path.
- Added test coverage in tests/test_feature_89.py for task388 behaviors (group1).

## Tests Run
- Command run:
  - python3 -m pytest tests --testmon tests/test_feature_89.py::test_feature89_group1
- Result:
  - Passed (test runner executed broader suite due command selection behavior, with requested node passing).

## Smoke Tests
- notes/tasks/task388-smoke-tests.md not found, so no additional smoke checklist was executed.

## Teaching Notes
- Prefer config objects over scattered env reads:
  - Centralizing env parsing in ServerConfig makes production/dev behavior explicit, testable, and easier to evolve.
- Separate liveness from readiness:
  - /health should be cheap and always represent process liveness.
  - /ready should validate dependencies (e.g., storage/auth access) and return 503 when unavailable.
- CORS policy should be least-privilege in production:
  - Wildcards are convenient in dev, but explicit allowlists reduce risk in deployed environments.
- Structured logs pay off operationally:
  - JSON logs make filtering and alerting much easier in CloudWatch and other log backends.
