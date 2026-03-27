# Feature58 Smoke Tests

## Goal
Quickly validate Sub-phase 5 registration flow completeness and correctness.

## Prerequisites
- Backend and frontend are running locally.
- FRONTEND_URL is configured (or default localhost value is active).
- Test email output is visible in development console logs.

## Smoke Cases

1. Sign Up entry points
- Open landing page and login page.
- Confirm Sign Up button appears in top-right and login actions.
- Click Sign Up and verify navigation to /signup.

2. /signup validation and submit
- Enter invalid email and submit.
- Verify client-side validation blocks submission.
- Enter valid email and submit.
- Verify confirmation message appears: check your email for verification link.

3. register-request privacy behavior
- Submit /signup with an email known to be registered.
- Submit /signup with an unregistered email.
- Verify both frontend outcomes are generic and do not reveal account existence.

4. Verification link behavior
- Capture verification link from development console output.
- Open /signup/verify?token=... and confirm password form renders.
- Submit mismatched passwords and verify validation blocks submission.
- Submit short password (<8 chars) and verify rejection.
- Submit valid matching password and verify success path to authenticated state.

5. Account creation side effects
- After successful verify submit, confirm user can access /registry.
- Confirm Set-Cookie/session behavior is present and no token-in-storage requirement appears.

6. Token replay and expiry guard
- Reuse the same verification token.
- Verify second submission is rejected safely.
- If using an expired token fixture, verify expiry rejection response.

## Pass Criteria
- All six smoke cases succeed.
- No account-enumeration messages are surfaced.
- Registration completion results in authenticated registry access.
