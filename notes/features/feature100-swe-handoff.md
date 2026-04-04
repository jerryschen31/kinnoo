# Feature 100 — SWE Handoff: Auth Hardening

## Context
Harden existing auth system with lockout, password policy, and token blacklist. The auth infrastructure already uses Argon2id and JWT (HMAC-signed, 60-min TTL).

## Files to Modify
- `server/storage/user_store.py` (~95 lines) — Add fields:
  - `failed_login_attempts: int`
  - `locked_until: datetime | None`
  - `password_changed_at: datetime | None`
- `server/routes/auth.py` (~300 lines) — Login endpoint:
  - Check lockout before attempting password verification
  - Increment `failed_login_attempts` on failure
  - Lock account after 5 consecutive failures (15-min lockout)
  - Reset counter on successful login
  - Registration: enforce password policy
- `server/auth/token.py` (~350 lines) — Add token blacklist:
  - In-memory `set()` of revoked token JTIs
  - `blacklist_token(jti: str, expires_at: datetime)` method
  - `is_blacklisted(jti: str) -> bool` check in token validation
  - Periodic cleanup of expired tokens from blacklist

## Password Policy
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character (!@#$%^&*...)
- Clear error message listing unmet requirements

## Implementation Notes
- Lockout response: 423 Locked with JSON body: `{"error": "account_locked", "retry_after": 900}`
- Lockout is per-user (not per-IP) — stored in user record
- Token blacklist is in-memory (acceptable for single Fargate task). Tokens expire naturally, so blacklist entries can be pruned after TTL.
- Add a JTI (JWT ID) claim to tokens if not already present — needed for blacklist tracking
- `POST /logout` should call `blacklist_token()` with the current token's JTI

## Testing
- 5 failed logins → account locked
- Login attempt on locked account → 423
- Wait 15 min (mock time) → account unlocked
- Successful login resets counter
- Weak password rejected with specific message
- Blacklisted token rejected by auth middleware
- Expired blacklist entries cleaned up

## Dependencies
- None

## Acceptance Criteria Summary
1. Account lockout after 5 failures, 15-min cooldown
2. Password policy enforcement on register and password change
3. Token blacklist on logout
4. Blacklisted tokens rejected by middleware
