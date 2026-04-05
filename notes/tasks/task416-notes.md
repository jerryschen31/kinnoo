# Task 416 Notes

## Summary
Implemented task416 by adding invite CLI commands and invite token lifecycle persistence APIs.

### Code changes
- Added `invite` command group in `server/cli.py`:
  - `invite create --email --days-valid`
  - `invite list`
- `invite create` now prints:
  - token
  - generated registration URL (`KINNOO_PUBLIC_BASE_URL` + `/register?token=...`)
  - expiration timestamp
- `invite list` prints compact operational table with status (`pending` / `consumed`).
- Added invite storage methods in `server/storage/user_store.py`:
  - `create_invite`
  - `list_invites`
  - `validate_invite`
  - `consume_invite`
- Invite records persisted in store root as `invites.json`.

## Tests Run
- python3 -m pytest --testmon tests/test_feature_102.py::test_feature102_group2
- Result: 1 passed

## Smoke Tests
- notes/tasks/task416-smoke-tests.md not found, so no additional smoke checklist was executed.

## Teaching Notes
- Separate invite lifecycle primitives from CLI parsing:
  - once `create/list/validate/consume` are in storage layer, API endpoints can reuse them later.
- Token UX matters operationally:
  - printing both raw token and full URL minimizes manual mistakes when sending invites.
- Status-focused tabular output scales better than raw JSON for on-call workflows:
  - operators can quickly spot stale/consumed invites at a glance.
