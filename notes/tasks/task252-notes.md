# Task252 - Publish optional pack-and-bump flow

## Summary
- Added publish CLI support for `--pack` and optional `--bump {major,minor,patch}`.
- Updated publish help text so it explicitly states: with `--pack`, `<target>` must be a file path to an agent directory.
- Implemented publish command behavior to:
  - validate `--bump` requires `--pack`,
  - execute pack first when `--pack` is used,
  - resolve agent name from the packed directory manifest,
  - continue with existing archive-first publish flow.
- Added focused task252 tests in `tests/test_publish_command.py`:
  - `test_publish_with_pack_packs_then_publishes`
  - `test_publish_with_pack_and_bump_publishes_bumped_version`
  - `test_publish_pack_bump_guardrail_errors`

## Files changed
- `src/kinnoo/cli.py`
- `src/kinnoo/publish_command.py`
- `tests/test_publish_command.py`
- `TASKS.txt`

## Targeted tests run
- `python3 -m pytest tests/test_publish_command.py::test_publish_with_pack_packs_then_publishes tests/test_publish_command.py::test_publish_with_pack_and_bump_publishes_bumped_version tests/test_publish_command.py::test_publish_pack_bump_guardrail_errors -q`
- Result: `3 passed`

## Teaching notes
- Keep backward compatibility by making new behavior opt-in (`--pack`) and preserving default archive-first behavior.
- Guardrails are easiest to maintain when enforced in both parser-level validation (choices/help) and command-level semantics (`--bump` requires `--pack`).
- For CLI UX features, include tests for both happy paths and operator mistakes (flag combos and missing prerequisites).
