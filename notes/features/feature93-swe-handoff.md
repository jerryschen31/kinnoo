# Feature 93 — SWE Handoff: CLI Command Reference

## Context
Create comprehensive CLI reference documentation covering all kinnoo and kinnoo-server commands.

## Files to Create
- `docs/cli-reference.md`

## Content Structure
For each command:
- **Usage**: `kinnoo <command> [args] [options]`
- **Description**: What the command does
- **Arguments**: Positional args with types
- **Options**: Flags with defaults and descriptions
- **Environment Variables**: Env vars that affect behavior
- **Exit Codes**: 0 = success, 1 = error, etc.
- **Examples**: 2-3 practical examples

## Commands to Document
### Client (kinnoo)
init, pack, install, run, publish, search, login, logout, keygen, trust, inspect, uninstall, list, version

### Server (kinnoo-server)
bootstrap, user create, user list, user reset-password, user unlock, user delete, invite create, invite list

## Implementation Notes
- Reference `src/kinnoo/cli.py` for client commands and argument definitions
- Reference `server/cli.py` for server commands
- Some server commands (from feature102) may not exist yet — mark as `[planned]`
- Include the `--help` output where useful

## Dependencies
- None (can document existing + planned commands)

## Acceptance Criteria Summary
1. docs/cli-reference.md with all client commands
2. Server commands section (existing + planned)
3. Cross-referenced from README.md
