# Feature 52 SWE Handoff - Secure Login UI, Validation, and Session-Cookie Submission Flow

## Goal
Implement the /login page and secure client behavior for login submission as specified in Sub-phase 2.

## Scope
- Parent feature: feature52
- Tasks: task294, task295, task296, task297
- Related tests: test437, test438, test439, test440, test441, test442
- Dependencies: feature50 + feature51

## Functional requirements
1. Centered minimalist login card.
2. Fields: Username (E-mail) and Password.
3. Forgot Password stub link to /forgot-password.
4. Client-side validation for required fields and email format.
5. Loading/disabled login button during in-flight request.
6. Request uses session-cookie model:
   - POST to /login (via Next.js proxy/rewrite)
   - fetch must include credentials
   - no localStorage/sessionStorage token storage
7. On success, navigate user to /registry.

## Task-by-task implementation guidance

### task294 - Login card UI and required fields
Files:
- web/app/(public)/login/page.tsx

Implement:
1. Card centered vertically/horizontally with dark theme styles.
2. Label + input for email and password.
3. Submit button text Login.
4. Forgot Password link to /forgot-password.

Done when:
- The route renders complete form controls with correct labels and link.

### task295 - Client-side validation and loading state
Files:
- web/app/(public)/login/page.tsx
- web/lib/auth-validation.ts

Implement:
1. Validate non-empty email and password.
2. Validate email format.
3. Show inline errors.
4. When submit starts, disable button and show loading state.
5. Reset loading state after response.

Done when:
- Invalid forms do not dispatch network requests.

### task296 - Secure submission through proxy
Files:
- web/app/(public)/login/page.tsx
- web/lib/auth-client.ts
- web/next.config.ts

Implement:
1. Submit to /login (not direct backend origin from the component).
2. Use fetch with credentials include.
3. Do not store auth tokens in browser storage.
4. On success, route to /registry.
5. Preserve compatibility with Set-Cookie from server response.

Done when:
- Success path reliably navigates to /registry in local test runs.

### task297 - Automated tests
Files:
- web/__tests__/login-page.test.tsx
- web/package.json

Implement:
1. Render test for email/password/button and forgot-password link.
2. Validation tests for empty + malformed inputs.
3. Loading-state test around delayed fetch.
4. Submission config test for credentials include.
5. Redirect test to /registry on success.

Done when:
- test437-test442 scenarios pass.

## Security guardrails
- Never write secrets/tokens to localStorage/sessionStorage.
- Do not expose sensitive server error payloads directly in UI.
- Keep error messages user-safe and generic.

## Non-goals for this feature
- Registry dashboard implementation (Sub-phase 3).
- Password reset backend implementation (Sub-phase 5); only stub link required here.
