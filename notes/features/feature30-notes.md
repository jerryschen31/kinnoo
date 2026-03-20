# Feature30 Notes

## Intent
Feature30 adds an authenticated web UI for browsing and downloading registry content, aligned with V1 authenticated-only read policy.

## Scope Implemented in Planning
- Updated feature definition and ACs in `FEATURES.txt`
- Added tasks `task245`-`task248`
- Added tests `test343`-`test346`

## UX and Security Model
- Session-authenticated pages only (no anonymous browsing)
- Secure cookies: HttpOnly, Secure, SameSite=Lax
- CSRF tokens required on all POST forms
- Routes:
  - `/login`
  - `/agents`
  - `/agents/{tenant}/{agent}`
  - `/search`

## Task-by-Task Implementation Guidance

### task245
- Configure Jinja2 and static assets.
- Build shared base template and style primitives.
- Keep design simple and maintainable.

### task246
- Implement login/logout session lifecycle.
- Redirect unauthenticated users to `/login`.
- Validate CSRF on form POSTs.

### task247
- Render paginated listing page using server metadata indexes.
- Implement search page and query filtering.
- Ensure only authorized-visible items are shown.

### task248
- Render per-agent profile/version history.
- Provide per-version download actions that redirect via presigned URL route.
- Show stable metadata fields clearly.

## Test Strategy
- `test343`: template engine and base layout
- `test344`: login/logout/session/CSRF
- `test345`: listing + search + auth guard
- `test346`: profile + download redirect flow

## SWE Risks
- Missing session guard on one or more pages
- CSRF checks not applied uniformly to forms
- Template rendering errors on empty states or unknown tenant/agent

## SWE Done Checklist
- Unauthenticated requests redirect to login for all browsing pages
- CSRF validation present for every POST route
- Web UI tests pass with TestClient
- Session invalidation works on logout/password reset paths
