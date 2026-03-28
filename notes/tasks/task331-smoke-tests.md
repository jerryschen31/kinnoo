# Task331 Smoke Tests

Date: 2026-03-25

## Scope
- Registry modal now supports two tabs: Registry Manifest (default) and Agent Manifest (kinnoo.yaml payload).
- Registry modal shows a terminal-like install command block with copy action.
- Search tab does not show "Unable to search agents right now" for blank query.

## Smoke Suite
1. Frontend registry/modal smoke suite
- Command:
```bash
cd /Users/jerry/gh/kinnoo/web && npm run test -- __tests__/agent-card-modal.test.tsx __tests__/registry-dashboard.test.tsx
```
- Expected:
  - Modal opens from Name click.
  - Registry Manifest and Agent Manifest tabs render.
  - Agent Manifest tab shows manifest fields from agent payload.
  - Install command block renders and copy button writes command to clipboard.
  - Blank search query does not render "Unable to search agents right now".
- Result: Passed (2 files, 10 tests).

2. Backend detail payload smoke suite
- Command:
```bash
cd /Users/jerry/gh/kinnoo && python3 -m pytest server/tests/test_agents_routes.py -q
```
- Expected:
  - Agent detail response includes latest_version and agent_manifest for latest published version.
- Result: Passed (1 passed).

3. Manifest integrity validation
- Command:
```bash
cd /Users/jerry/gh/kinnoo && python3 src/validate_project_manifests.py
```
- Expected:
  - TASKS/FEATURES/TESTS manifests remain valid after task331 addition.
- Result: Passed (Validation passed).

## Notes
- One test iteration was required: search-based modal tests were updated to enter a non-empty query before asserting search results because blank queries now intentionally short-circuit to an empty state.
