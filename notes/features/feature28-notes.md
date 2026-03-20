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
