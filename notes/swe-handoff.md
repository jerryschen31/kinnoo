# SWE Handoff — Feature 115: UAT Part 1 CLI Hardening

See [notes/features/feature115-notes.md](../features/feature115-notes.md) for the full handoff brief
including implementation priority, recommended batch order, design constraints, and affected files.

## Quick Reference

- **Feature:** feature115 — UAT Part 1: CLI hardening
- **Tasks:** task453–task485 (33 tasks)
- **Tests:** test628–test671 (44 tests)
- **Source UAT:** `notes/phases/phase13-sat-uat-updates.md` (annotated with `[taskXXX]` references)
- **Batch count:** 7 implementation batches

## Batch Summary

1. **Quick wins** (task453, task476, task472) — CLI help version/icon, comment out daemon cmds, rename --sandbox
2. **Init refactor** (task454–459) — positional framework arg, wizard, main.py entrypoint, templates, .gitignore
3. **Pack enhancements** (task460–464) — data/ exclude, --include/--exclude, --preflight, help text, --sign merge, --json
4. **Publish/Install/Run** (task465–471) — mutual exclusion, version history, remove deprecated, --json flags, structured output
5. **Inspect** (task473–475) — --json, --update 2-arg, confirmation prompt
6. **Search/List + new commands** (task477–478, task484–485) — --json, kinnoo fetch, kinnoo uninstall
7. **Registry UI & server security** (task479–483) — security column, server-side checks, containerized Lambda, Security tab
