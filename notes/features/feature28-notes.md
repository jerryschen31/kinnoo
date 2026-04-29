# Feature28 Notes

## Intent
Feature28 introduces a clean client-side abstraction for registry operations so local and remote modes can coexist without behavior regressions.

## Scope Implemented in Planning
- Added/updated feature definition and ACs in `FEATURES.txt`
- Added tasks `task229`-`task233`
- Added tests `test327`-`test331`

## Acceptance Criteria Interpretation
- AC1/AC2: protocol seam exists and local behavior remains unchanged
- AC3: remote client uses tenant-aware pathing
- AC4: config + env precedence covers URL/token/tenant
- AC5/AC6: deterministic local/remote selection and auth usage
- AC7: strict regression preservation for local commands
- AC8: complete HTTP error taxonomy with actionable UX

## Task-by-Task Implementation Guidance

### task229
- Create `RegistryBackend` as Python Protocol in a new module.
- Refactor existing local registry code into `LocalRegistryBackend` with no external behavior changes.
- Keep compatibility wrappers if existing callers import old functions.

### task230
- Implement `RemoteRegistryClient` with urllib.request to avoid additional dependency coupling.
- Centralize request builder for consistent auth headers and timeout behavior.
- Keep response parsing strict; validate expected keys per endpoint.

### task231
- Add config keys: `registry_url`, `registry_token`, `tenant_slug`.
- Env override order: env first, then config file.
- Fail with clear guidance if remote mode is selected but token/tenant missing.

### task232
- Backend selection matrix:
  - `--local` forces local backend
  - `--remote` forces remote backend
  - no explicit flag: remote if configured, else local
- Preserve existing command output messages where possible.

### task233
- Map each HTTP failure class to a stable user-facing message and error code.
- Include retry guidance for 429 and transient 5xx failures.
- Avoid exposing raw tracebacks for expected HTTP failures.

## Test Strategy
- `test327`: protocol + local behavior preservation
- `test328`: request/endpoint contract for remote client
- `test329`: config/env precedence
- `test330`: command-level backend selection behavior
- `test331`: error-mapping completeness and clarity

## SWE Risks
- Breaking local behavior while refactoring to protocol
- Inconsistent auth header usage across methods
- Ambiguous backend selection when flags/config conflict

## SWE Done Checklist
- Local regression suite unchanged
- All feature28 tests pass
- Command help/docs updated for remote config fields

## Tech Lead Review 1

### Scope and Traceability
- Feature/task/test linkage exists as planned:
  - `FEATURES.txt`: `feature28` references `task229`-`task233`
  - `TASKS.txt`: `task229`-`task233` reference `test327`-`test331`
  - `TESTS.txt`: `test327`-`test331` exist and point to concrete automated checks
- Manifest integrity gate passed: `python3 scripts/validate_project_manifests.py`

### Gate Checklist Results (Feature28)
- [x] Scope sanity: Tasks `task229`-`task233` and tests `test327`-`test331` are present and linked.
- [x] Local regression safety: local `publish/install/list/search` paths remain covered and passing.
- [x] Remote contract: tenant-aware remote pathing and Authorization header behavior are implemented in remote client flows.
- [x] Config precedence: env overrides config for URL/token/tenant (`KINNOO_REGISTRY_URL`, `KINNOO_REGISTRY_TOKEN`, `KINNOO_TENANT_SLUG`).
- [x] Error UX: 401/403/404/409/429/500 and network error paths map to actionable user-facing messages.
- [x] Approval decision: `APPROVE`.

### Regression and Security Evidence
- Full requested regression command executed: `python3 -m pytest --testmon`
  - Result: `69 passed, 1 skipped, 24 deselected`
- Sensitive-data scan executed across `server/` with broad credential/token/private-key patterns.
  - Matches were expected security-domain identifiers and test fixtures; no hardcoded real secrets, private keys, or leaked credentials were found.

### Findings and Follow-ups
- No blocking functional or security findings for feature28.
- Manifest workflow hygiene follow-up: `task229`-`task233` statuses in `TASKS.txt` still read `not-started` and should be advanced in the normal Tech Lead/Git workflow to reflect implementation/review state.

### Recommendation
- `APPROVE` for merge readiness for feature28, with the non-blocking status-hygiene follow-up tracked.
