# Task397 Notes

## Summary
- Expanded `docs/cli-reference.md` with implemented `kinnoo-server` command coverage:
  - `bootstrap`
  - `user create`
  - `user list`
  - `user reset-password`
  - `invite create`
- Added an "Additional server commands" section for currently implemented extras (`user unlock`, `user delete`, `invite list`).
- Added README cross-reference to `docs/cli-reference.md`.

## Why
- Task397 covers feature93 AC4/AC5: server command coverage and README cross-reference.
- Documentation is based on actual `server/cli.py` behavior and avoids claiming unsupported commands.

## Tests Run
- `python3 -m pytest tests --testmon -k "test_feature93_group2"`
- Result: 1 passed.

## Teaching Notes
- For server CLI docs, prefer documenting invocation patterns that work from source (`python3 -m server.cli ...`) unless an installed console script is guaranteed.
- Grouping implemented vs planned command surfaces clearly reduces onboarding confusion for operators and developers.
