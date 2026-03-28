# Feature59 SWE Handoff

## Scope
Implement complete forgot-password and password-reset workflows:
- Public pages:
  - /forgot-password
  - /forgot-password/reset
- Backend endpoints:
  - POST /api/auth/password-reset-request
  - POST /api/auth/password-reset-confirm
- Session invalidation after successful password reset.

## Why This Feature Exists
Users must be able to securely recover account access without exposing whether an email is registered.

## Tasks In This Feature
- task323: Build forgot-password pages and link wiring
- task324: Implement POST /api/auth/password-reset-request endpoint
- task325: Implement POST /api/auth/password-reset-confirm endpoint
- task326: Add forgot-password integration and component tests

## Implementation Guidance By Task

### task323
Key outcomes:
- Login page "Forgot your password?" routes to /forgot-password.
- /forgot-password page:
  - centered card with email field and Send Reset Link action,
  - generic confirmation message after submit.
- /forgot-password/reset page:
  - New Password + Confirm Password,
  - client validation for match + min length.

### task324
Key outcomes:
- POST /api/auth/password-reset-request accepts email.
- Looks up user for known-account token creation.
- Generates signed expiring reset token.
- Builds link using FRONTEND_URL:
  - {FRONTEND_URL}/forgot-password/reset?token={token}
- Sends link through EmailService abstraction.
- Always returns generic success regardless of account existence.

### task325
Key outcomes:
- POST /api/auth/password-reset-confirm accepts token + new_password.
- Validates token signature, expiry, and single-use state.
- Updates user password hash.
- Consumes token.
- Invalidates all existing sessions for user.
- Returns success contract consumable by frontend redirect to /login with success state.

### task326
Key outcomes:
- Endpoint tests for reset-request and reset-confirm happy/failure cases.
- Explicit privacy tests for unknown email response parity.
- Rate-limit tests for reset-request.
- Component tests for forgot-password pages and validation UX.

## Required API Contracts
- POST /api/auth/password-reset-request
  - Input: { email }
  - Output: generic success message
- POST /api/auth/password-reset-confirm
  - Input: { token, new_password }
  - Output: success state for login redirect; safe failures for invalid token states

## Security Constraints
- No account enumeration via response differences.
- Token replay prevention through consumed-state checks.
- Reset must invalidate existing sessions.
- Password updates must always store hashed form.

## Linked Tests
- test475, test476, test477, test478, test479, test480, test481

## Suggested SWE Execution Order
1. task323
2. task324
3. task325
4. task326

## Completion Checklist
- Forgot-password pages and route wiring implemented.
- Reset endpoints implemented with privacy and token protections.
- Session invalidation verified.
- Linked tests pass and are deterministic.
