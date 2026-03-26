# Task328 Notes

## Scope completed
- Added EmailService abstraction and development console provider:
  - `server/services/email_service.py`
  - `server/services/email_console.py`
- Refactored auth routes to dispatch registration/reset links through EmailService instead of direct sink writes.
- Added configuration fields for `FRONTEND_URL`, register token secret, and password-reset token secret.
- Updated app bootstrap to wire EmailService and to resolve token secrets from config/env without hardcoded static fallback literals.

## Tests added and coverage
- `tests/test_registry.py::test_feature60_email_service_abstraction_dev_provider`
  - Verifies register-request and password-reset-request both dispatch through the dev provider and log expected links.
- `tests/test_registry.py::test_feature60_env_secrets_and_single_use_tokens`
  - Verifies env-configured token secrets are used.
  - Verifies register-confirm and reset-confirm enforce single-use token behavior.
  - Verifies generated links respect configured `FRONTEND_URL`.

## Targeted regression command and result
Command:
```bash
cd /Users/jerry/gh/kinnoo && python3 -m pytest tests --testmon -k "test_feature60_email_service_abstraction_dev_provider or test_feature60_env_secrets_and_single_use_tokens"
```

Result:
```text
2 passed
446 deselected
```

## Teaching notes
- Email dispatch should be an interface boundary: route handlers orchestrate domain flow while providers handle transport details (console/SES/SendGrid).
- Driving security-sensitive values from config/env keeps behavior explicit and testable; tests should assert both value wiring and runtime outcomes.
- Single-use token enforcement is best validated as a two-step behavioral test (success then replay failure), not just by checking DB writes.
