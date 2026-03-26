# Task 325 Smoke Tests

## Goal
Validate password reset confirmation enforces policy and invalidates all active sessions.

## Preconditions
- Existing user account with at least two active sessions.
- Valid reset token generated from password-reset-request flow.

## Manual smoke checks
1. Open /forgot-password and submit the account email.
2. Open reset link and attempt invalid password cases:
   - shorter than 10 chars
   - password too similar to email/username
3. Submit valid new password and complete reset.
4. Confirm redirect returns to /login with success indicator.
5. Try using previously active sessions and verify they are rejected.
6. Log in with new password and verify login succeeds.

## Pass criteria
- Invalid password attempts are blocked with safe feedback.
- Successful reset updates password and revokes all prior sessions.
