# Feature 55 SWE Handoff - BFF Proxy Integration, CSRF Pass-through, and Auth Route Guard

## Scope
- Feature: feature55
- Tasks: task307, task308, task309, task310
- Tests: test453, test454, test455, test456, test457, test458
- Depends on: feature54

## Goal
Finish core frontend-backend integration for Sub-phase 4:
1. proxy rewrites to backend via BACKEND_URL,
2. CSRF pass-through for login and authenticated POST,
3. /api/auth/me endpoint,
4. app/(auth)/layout.tsx redirect guard.

## Task details

### task307 - Rewrites + env contract
Implement in:
- web/next.config.ts
- web/.env.example

Requirements:
- Rewrite /api/* to BACKEND_URL (fallback http://localhost:8000).
- Preserve session-cookie flow expectations.
- Ensure forwarding semantics needed for X-Forwarded-For and X-Request-Id.

### task308 - CSRF forwarding
Implement in:
- web/app/(public)/login/page.tsx
- web/lib/auth-client.ts
- web/app/(auth)/registry/page.tsx

Requirements:
- Login CSRF hidden field must survive BFF path.
- Session CSRF token (kinnoo_csrf) forwarded in POST actions via header or form field.

### task309 - /api/auth/me endpoint
Implement in:
- server/routes/api.py
- server/auth/middleware.py

Requirements:
- Validate session cookie.
- Return { user_id, tenant_slug, username } on success.
- Return 401 when invalid.

### task310 - Auth route guard
Implement in:
- web/app/(auth)/layout.tsx
- web/lib/auth-client.ts

Requirements:
- Server-side call to /api/auth/me.
- Redirect to /login on 401.
- Render children on success.

## Acceptance criteria mapping
- AC1 -> test453
- AC2 -> test454
- AC3 -> test455
- AC4 -> test456
- AC5 -> test457
- AC6 -> test458
- AC7 -> test458

## Notes
- Keep session-cookie model. No token storage in localStorage/sessionStorage.
- Keep behavior compatible with existing backend auth/session services.
