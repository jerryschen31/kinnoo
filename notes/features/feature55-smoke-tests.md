# Feature 55 Smoke Tests - BFF, CSRF, and Auth Guard

## 1) Rewrite and backend routing
1. Configure BACKEND_URL.
2. Hit frontend /api/* path from browser or curl.
3. Confirm backend receives request.

Pass if:
- Request resolves through configured backend URL.

## 2) Login CSRF pass-through
1. Submit login form through frontend.
2. Verify backend login CSRF validator accepts request.

Pass if:
- Valid login CSRF flow succeeds through proxy.

## 3) Session CSRF for authenticated POST
1. Trigger authenticated POST action.
2. Verify kinnoo_csrf token is forwarded in header or form.

Pass if:
- Backend accepts valid CSRF token; rejects missing token.

## 4) /api/auth/me contract
1. Call /api/auth/me with valid session.
2. Call with invalid/missing session.

Pass if:
- Valid returns user_id, tenant_slug, username.
- Invalid returns 401.

## 5) Auth layout redirect
1. Force /api/auth/me to return 401 in auth context.
2. Open /registry.

Pass if:
- Redirect lands on /login.

## 6) No browser token storage
1. Perform login/auth flow.
2. Inspect localStorage and sessionStorage.

Pass if:
- No auth tokens are stored there.
