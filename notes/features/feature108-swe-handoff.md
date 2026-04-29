# Feature 108 — SWE Handoff: Invite-Only Registration

## Context
Modify registration to require a valid invite token. Tokens generated via admin CLI (feature102).

## Files to Modify
- `server/routes/auth.py` (~300 lines) — Registration endpoint:
  - Add `invite_token` required parameter to `POST /register`
  - Validate token against invite store before creating user
  - Consume (mark used) token on successful registration
  - Return 403 if token is missing, invalid, or expired
- `server/routes/web_auth.py` (~230 lines) — Web registration page:
  - Add invite token field to registration form
  - Pre-fill from `?token=` URL query parameter
  - Show validation errors
- `server/storage/user_store.py` — Invite token storage (may already exist from feature102):
  - `validate_invite(token) -> InviteToken | None`
  - `consume_invite(token) -> bool`

## Registration Flow
1. Jerry runs: `kinnoo-server invite create --email user@example.com --days-valid 30`
2. Jerry sends invite URL to user: `https://dev.kinnoo.ai/register?token=abc123xyz`
3. User visits URL → registration form with token pre-filled
4. User fills email + password → `POST /register` with `invite_token=abc123xyz`
5. Server validates token → creates user → consumes token
6. User can now login

## Implementation Notes
- Invite tokens are single-use: consumed on successful registration
- Expired tokens return 403 with "Invite token has expired"
- Invalid/missing tokens return 403 with "Valid invite token required"
- Token validation must be atomic (check + consume in one operation to prevent race conditions)
- Consider using file-based locking or SQLite transaction for atomicity
- The `invite_token` field should also be accepted in CLI login flow (`kinnoo register --invite-token`)

## Testing
- Valid token → registration succeeds, token consumed
- Reused token → 403 "already used"
- Expired token → 403 "expired"
- Missing token → 403 "required"
- Invalid token → 403 "invalid"
- Pre-fill from URL query parameter

## Dependencies
- feature102 (admin CLI creates invite tokens and storage)

## Acceptance Criteria Summary
1. Registration requires invite_token
2. Tokens are single-use, expire after configured duration
3. Web form pre-fills token from URL
4. 403 for missing/invalid/expired tokens
