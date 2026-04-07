# Kinnoo Server CLI Reference

This reference documents the current Kinnoo server command-line interface.

- Server CLI: `kinnoo-server`
- Implementation location: `server/cli.py`

## Conventions

- Exit code `0`: command completed successfully.
- Exit code non-zero: command failed validation or runtime execution.

## Server Commands (`kinnoo-server`)

### bootstrap

- Usage: `python3 -m server.cli bootstrap [--store-root <path>] [--username <name>]`
- Description: Create first admin account in server persistence store.
- Arguments: none.
- Options: `--store-root`, `--username`.
- Env vars: none required.
- Exit codes: non-zero on bootstrap failure.
- Examples:
  - `python3 -m server.cli bootstrap --store-root ./server-data --username admin`

### user create

- Usage: `python3 -m server.cli user create --email <email> [--role {admin,user}] [--store-root <path>]`
- Description: Create a user and print temporary password.
- Arguments: none.
- Options: `--email`, `--role`, `--store-root`.
- Env vars: none required.
- Exit codes: non-zero on duplicate/validation errors.
- Examples:
  - `python3 -m server.cli user create --email dev@example.com`

### user list

- Usage: `python3 -m server.cli user list [--store-root <path>]`
- Description: List users with lock status and derived tenant.
- Arguments: none.
- Options: `--store-root`.
- Env vars: none required.
- Exit codes: zero for successful listing, including empty list.
- Examples:
  - `python3 -m server.cli user list --store-root ./server-data`

### user reset-password

- Usage: `python3 -m server.cli user reset-password --email <email> [--store-root <path>]`
- Description: Reset a user password and print a new temporary password.
- Arguments: none.
- Options: `--email`, `--store-root`.
- Env vars: none required.
- Exit codes: non-zero when target user is not found.
- Examples:
  - `python3 -m server.cli user reset-password --email dev@example.com`

### invite create

- Usage: `python3 -m server.cli invite create --email <email> [--days-valid <n>] [--store-root <path>]`
- Description: Create an invite token for invite-only registration flow.
- Arguments: none.
- Options: `--email`, `--days-valid`, `--store-root`.
- Env vars: `KINNOO_PUBLIC_BASE_URL` (used to format output invite URL).
- Exit codes: non-zero on invite validation errors.
- Examples:
  - `python3 -m server.cli invite create --email teammate@example.com --days-valid 7`

### Additional server commands (implemented)

- `user unlock`
- `user delete`
- `invite list`
