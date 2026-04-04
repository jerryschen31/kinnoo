# Feature 102 — SWE Handoff: Admin CLI for User Management

## Context
Extend `server/cli.py` (~60 lines, currently has bootstrap only) with admin commands for managing users and invite tokens.

## Files to Modify
- `server/cli.py` (~60 lines) — Add subcommands under `user` and `invite` groups
- `server/storage/user_store.py` (~95 lines) — Add methods:
  - `create_user(email, password, tenant) -> User`
  - `list_users() -> list[User]`
  - `reset_password(email, new_password) -> bool`
  - `unlock_user(email) -> bool`
  - `delete_user(email) -> bool`
  - `create_invite(email, days_valid) -> InviteToken`
  - `list_invites() -> list[InviteToken]`
  - `validate_invite(token) -> InviteToken | None`
  - `consume_invite(token) -> bool`

## CLI Commands

### User Management
```bash
kinnoo-server user create --email bob@example.com
# Output: Created user bob@example.com
#         Tenant: bob
#         Temporary password: Xk9$mP2qR7!fL4nW

kinnoo-server user list
# Output:
# EMAIL                STATUS    TENANT    CREATED
# bob@example.com      active    bob       2026-04-01
# alice@example.com    locked    alice     2026-04-02

kinnoo-server user reset-password --email bob@example.com
# Output: New temporary password: Yp3$nQ8wT5!gK2mZ

kinnoo-server user unlock --email bob@example.com
# Output: Unlocked bob@example.com (was locked since 2026-04-04 10:30)

kinnoo-server user delete --email bob@example.com
# Output: Are you sure you want to delete bob@example.com? (y/N): y
#         Deleted bob@example.com
```

### Invite Management
```bash
kinnoo-server invite create --email user@example.com --days-valid 30
# Output: Invite token: abc123xyz
#         URL: https://dev.kinnoo.ai/register?token=abc123xyz
#         Expires: 2026-05-04

kinnoo-server invite list
# Output:
# EMAIL                TOKEN       EXPIRES      STATUS
# user@example.com     abc123x...  2026-05-04   pending
```

## Implementation Notes
- Use argparse subparsers (consistent with existing CLI pattern)
- Temporary passwords: `secrets.token_urlsafe(16)` — random 16-char strings
- Invite tokens: `secrets.token_urlsafe(32)` — random, URL-safe
- All commands operate directly on the auth store file (no HTTP)
- `user delete` requires interactive confirmation (or `--force` flag)
- Tenant is derived from email (local part before @, sanitized)

## Testing
- Create user → user exists in store
- List users → correct output format
- Reset password → old password no longer works, new one does
- Unlock → locked_until is cleared
- Delete → user removed from store
- Create invite → invite token stored
- List invites → correct format

## Dependencies
- feature100 (lockout fields in user store)

## Acceptance Criteria Summary
1. user create/list/reset-password/unlock/delete commands
2. invite create/list commands
3. Clear output formatting
4. Operates directly on auth store
