# Feature58 SWE Handoff

## Scope
Implement the Sub-phase 5 sign-up workflow end-to-end:
- Sign Up CTA routing to /signup.
- /signup email capture flow.
- /signup/verify password creation flow.
- Backend endpoints:
  - POST /api/auth/register-request
  - POST /api/auth/register-confirm
- Session creation on successful registration and redirect compatibility with /registry.

## Why This Feature Exists
This feature introduces self-service account creation while preserving privacy and security:
- No account-enumeration leaks in register-request responses.
- Signed, expiring, single-use verification tokens.
- Immediate authenticated user experience after successful confirmation.

## Tasks In This Feature
- task319: Add Sign Up CTA and create /signup + /signup/verify pages
- task320: Implement POST /api/auth/register-request endpoint
- task321: Implement POST /api/auth/register-confirm endpoint
- task322: Add registration integration and component tests

## Implementation Guidance By Task

### task319
Key outcomes:
- Sign Up appears in shared top-right nav and login page action area.
- /signup page:
  - centered minimalist card matching login style,
  - email field,
  - valid email client validation,
  - submit action for sending verification link.
- /signup/verify page:
  - token-driven page,
  - Create Password + Confirm Password,
  - client validation: match + minimum length >= 8.

Notes:
- Keep visual language aligned with existing public auth pages.
- Reuse shared form components where possible.

### task320
Key outcomes:
- POST /api/auth/register-request accepts email payload.
- Duplicate-safe behavior with non-enumerating generic success response.
- Signed verification token with time-based expiry.
- Verification link built from FRONTEND_URL:
  - {FRONTEND_URL}/signup/verify?token={token}
- Email dispatch goes through EmailService (from feature60 foundation).

Notes:
- Do not disclose whether email already exists.
- Keep token creation logic centralized in auth token service.

### task321
Key outcomes:
- POST /api/auth/register-confirm accepts token + password.
- Validates token signature, expiry, and single-use state.
- Creates user with hashed password.
- Creates default tenant slug from email prefix.
- Marks token consumed.
- Creates session and returns Set-Cookie contract so frontend can continue to /registry.

Notes:
- Ensure operations are safe against token replay.
- Keep tenant slug creation deterministic and normalized.

### task322
Key outcomes:
- Endpoint tests for:
  - register-request happy path,
  - duplicate-safe generic response,
  - request rate limiting,
  - register-confirm success,
  - expired/used token failures.
- Component tests for /signup and /signup/verify validations.
- Regression check that login/registry baseline behavior still works.

## Required API Contracts
- POST /api/auth/register-request
  - Input: { email }
  - Output: generic success message (always safe/non-enumerating)
- POST /api/auth/register-confirm
  - Input: { token, password }
  - Output: success response with session cookie semantics; error response for invalid token states

## Security Constraints
- Never reveal account existence.
- Token validation must include signature + expiry + consumed state.
- Password hashing required; no plaintext persistence.
- Follow rate limiting expectations tied to request endpoint.

## Linked Tests
- test467, test468, test469, test470, test471, test472, test473, test474

## Suggested SWE Execution Order
1. task319
2. task320
3. task321
4. task322

## Completion Checklist
- Sign Up CTA and pages implemented.
- Register endpoints implemented with security constraints.
- Session issuance and redirect path validated.
- Linked tests pass and are deterministic.
