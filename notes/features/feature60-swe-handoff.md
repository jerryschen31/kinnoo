# Feature60 SWE Handoff

## Scope
Implement shared foundations and hardening for Sub-phase 5:
- EmailService abstraction with development console provider.
- Environment-driven FRONTEND_URL for verification/reset links.
- Environment-driven token secrets.
- Single-use token consumption guarantees.
- Rate limiting on register-request and password-reset-request.
- Consolidated integration and regression coverage.

## Why This Feature Exists
Feature58 and feature59 depend on consistent security and operability primitives. This feature ensures those primitives are explicit, reusable, and test-covered.

## Tasks In This Feature
- task327: Introduce EmailService abstraction and development console provider
- task328: Add env-based token secrets, FRONTEND_URL config, and single-use token store
- task329: Apply endpoint rate limits for register-request and reset-request
- task330: Finalize Sub-phase 5 integration and regression test suite

## Implementation Guidance By Task

### task327
Key outcomes:
- EmailService interface defines registration and reset email dispatch operations.
- Console-backed development provider logs links for local workflows.
- Endpoint code depends on abstraction, not concrete provider.
- Provider selection is configuration-driven to support future SES/SendGrid.

### task328
Key outcomes:
- FRONTEND_URL config with default http://localhost:3000.
- Token signing secrets read from environment vars.
- Shared token lifecycle supports consumed-state checks.
- Register-confirm and reset-confirm mark tokens consumed on success.

Notes:
- Keep secret names centralized in config module.
- Do not hardcode fallback secrets.

### task329
Key outcomes:
- Register-request and password-reset-request both rate-limited per IP.
- Default policy target 5 requests/min/IP.
- Deterministic responses and tests for threshold behavior.

### task330
Key outcomes:
- Consolidated Sub-phase 5 suite validates AC coverage across feature58-60.
- Includes non-regression assertion for baseline login and registry flows.
- Provides stable CI entrypoint for future pipeline integration.

## Security Constraints
- Secret values must never appear in logs or API responses.
- Tokens must be single-use and replay-safe.
- Rate limit behavior must not leak whether account exists.

## Linked Tests
- test470, test477, test482, test483, test484

## Suggested SWE Execution Order
1. task327
2. task328
3. task329
4. task330

## Completion Checklist
- Email abstraction in place and wired for both auth flows.
- Env-based link and token secret config complete.
- Single-use token behavior validated.
- Request rate limits enforced and tested.
- Consolidated suite passes.
