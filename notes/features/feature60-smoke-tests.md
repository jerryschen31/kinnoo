# Feature60 Smoke Tests

## Goal
Validate shared Sub-phase 5 security and platform-hardening behavior.

## Prerequisites
- Backend running with auth env config.
- FRONTEND_URL set or default active.
- Token secret env vars configured for registration and reset flows.

## Smoke Cases

1. EmailService abstraction wiring
- Trigger register-request and password-reset-request.
- Verify both flows use development email provider output path.
- Confirm no direct hardcoded provider calls are required in endpoint handlers.

2. FRONTEND_URL link construction
- Inspect verification and reset links emitted in development logs.
- Verify links are rooted at FRONTEND_URL value.
- Verify fallback behavior works when FRONTEND_URL is unset (localhost default).

3. Env-based token secrets
- Start service without token secret env vars and verify expected config failure behavior.
- Start service with env vars and verify token operations succeed.
- Confirm no token secret values are printed in logs.

4. Single-use token enforcement
- Execute successful register-confirm once, then retry same token.
- Execute successful reset-confirm once, then retry same token.
- Verify retries fail due to consumed-token checks.

5. Rate limiting on request endpoints
- Send repeated requests to register-request from same IP until threshold+1.
- Send repeated requests to password-reset-request from same IP until threshold+1.
- Verify over-threshold responses are rate-limited in both flows.

6. Sub-phase 5 regression gate
- Run all Sub-phase 5 endpoint/component tests.
- Verify baseline login and /registry access workflows still pass.
- Confirm no regressions to existing session-cookie auth behavior.

## Pass Criteria
- All six smoke cases pass.
- Shared security controls are active and observable.
- Sub-phase 5 flows are complete and regression-safe.
