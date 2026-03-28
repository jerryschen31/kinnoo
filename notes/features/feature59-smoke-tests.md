# Feature59 Smoke Tests

## Goal
Quickly validate forgot-password and password-reset workflow completeness.

## Prerequisites
- Backend and frontend are running locally.
- Development console email logging is enabled.
- At least one known user account exists.

## Smoke Cases

1. Forgot password navigation
- Open /login and click Forgot your password?.
- Verify navigation to /forgot-password.

2. /forgot-password form behavior
- Submit invalid email format and verify client validation.
- Submit valid known email and verify generic confirmation message.
- Submit valid unknown email and verify same generic confirmation message.

3. Reset link generation
- For known email, capture reset link from console output.
- Verify link format includes /forgot-password/reset?token=...

4. /forgot-password/reset validation
- Open reset link page.
- Submit mismatched passwords and verify blocked submit.
- Submit short password (<8 chars) and verify rejection.
- Submit valid matching password and verify success response.

5. Reset confirmation side effects
- After successful reset, verify redirect or return path to /login success state.
- Attempt login with old password (should fail).
- Attempt login with new password (should succeed).

6. Session invalidation
- Maintain an existing session for the same user before reset.
- Complete reset.
- Verify previous session is invalidated and requires re-authentication.

7. Invalid token handling
- Retry consumed token and verify safe failure.
- Use expired or malformed token and verify safe failure without sensitive details.

## Pass Criteria
- All seven smoke cases succeed.
- Unknown email requests remain non-enumerating.
- Password reset invalidates old sessions and enables login with new password.
