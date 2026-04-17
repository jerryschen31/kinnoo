# Phase 9 Features Review Notes

## Tech Lead Review 1

Date: 2026-04-04
Reviewer: techlead-agent
Scope: feature89-feature91, feature100-feature102

### What I reviewed
- Planning baseline for Phase 9 in `notes/phases/phase8-planning-3.md`.
- Manifest definitions and status linkage in `FEATURES.txt`, `TASKS.txt`, `TESTS.txt`.
- Implemented code paths in `server/` and phase-specific tests in `tests/test_feature_89.py` through `tests/test_feature_102.py`.
- Secret/credential exposure risk scan across tracked files.
- Full regression suite.

### Validation executed
- Manifest validator:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python scripts/validate_project_manifests.py`
  - Result: PASS
- Full regression:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests`
  - Result: PASS (`516 passed, 10 skipped`)

### Findings (ordered by severity)

1. High - feature100 is only partially implemented and should not be treated as complete
- Evidence:
  - `FEATURES.txt` keeps feature100 at `status: not-started`.
  - In `TASKS.txt`, task410 is `needs-review`, but task411 and task412 remain `not-started`.
  - `tests/test_feature_100.py` has placeholders for `test_feature100_group2` and `test_feature100_group3` (no substantive assertions).
- Impact:
  - AC4/AC5 (password policy enforcement/guidance) and AC6-AC8 (logout blacklist/rejection/pruning) are not validated as implemented for this feature.
- Assessment:
  - This is a major gap relative to Phase 9 plan and requires completing task411/task412 before feature100 can move to `needs-review`.

2. Medium - feature101 AC5/AC7/AC8 coverage is shallow
- Evidence:
  - `tests/test_feature_101.py::test_feature101_group2` checks compose file presence and port mapping only.
- Impact:
  - AC5 (image size <200MB), AC7 (`docker compose up` reachability), AC8 (build/start/healthcheck runtime validation) are not fully exercised by current automated tests.
- Assessment:
  - Implementation exists, but verification depth is below stated AC intent.

3. Medium - feature102 AC8/AC9 input-validation coverage is partial
- Evidence:
  - `tests/test_feature_102.py` validates happy paths plus one invalid case (`--days-valid 0`).
  - No explicit CLI tests for malformed email input behavior or interactive delete confirmation rejection path.
- Impact:
  - Coverage does not fully substantiate broad AC language: "All commands validate inputs and print clear error messages.".

4. Low - feature89 description mentions HTTPS redirect middleware but AC set omits it
- Evidence:
  - feature89 description includes "Add HTTPS redirect middleware", but acceptance criteria AC1-AC7 and tests do not include it.
- Impact:
  - Potential requirement ambiguity between description and enforceable AC/test scope.

### Phase 9 planning alignment check (from phase8-planning-3)
- feature89: implemented, tests present, status `needs-review`.
- feature90: implemented, tests present, status `needs-review`.
- feature91: implemented, tests present, status `needs-review`.
- feature100: partially implemented only (task410 done); tasks 411/412 pending.
- feature101: implemented, tests present but AC verification depth gap noted above, status `needs-review`.
- feature102: implemented, tests present with validation-depth gap noted above, status `needs-review`.

Conclusion:
- Phase 9 is mostly delivered for 89/90/91/101/102, but feature100 is not complete and remains a Phase 9 blocker for full security-hardening scope.

### Security review (tokens/credentials/passwords exposure)
- Repo-wide pattern scan found many secret-like strings in tests/docs/scripts, but these appear to be fixtures, placeholders, or instructional examples (not live credentials).
- No evidence found of real production tokens/passwords committed in Phase 9 implementation files.
- Minor hardening applied in this review to reduce accidental secret-like literals in compose configuration (see fixes section).

### Minor fixes applied during review
1. Fixed feature102 runtime bug in `server/cli.py`
- Problem:
  - `kinnoo-server user list` referenced non-existent `User.tenant_slug`, causing runtime failure.
- Fix:
  - Derive tenant slug from username via `username_to_tenant_slug(user.username)`.

2. Removed hardcoded secret literals from `docker-compose.yml`
- Problem:
  - Compose file contained inline dev secret values.
- Fix:
  - Switched to required environment-variable expansion:
    - `${REGISTRY_TOKEN_SIGNING_SECRET?set-in-shell-or-.env}` etc.

3. Fixed unrelated minor regression discovered by full-suite run in `src/kinnoo/templates.py`
- Problem:
  - Generated MCP client template crashed if `python-dotenv` was not installed.
- Fix:
  - Made `load_dotenv` import optional with safe fallback no-op.

4. Updated legacy publish test fixtures in `tests/test_registry.py`
- Problem:
  - Older test manifests omitted `framework`, conflicting with newer server-side required field validation.
- Fix:
  - Added `framework: generic` to affected fixture manifests.

### Recommendation to proceed
- Keep feature89/90/91/101/102 in `needs-review` pending AC-depth refinements for feature101/102 tests.
- Do not advance feature100 to `needs-review` until task411 and task412 are implemented and tested.
- Add focused tests for:
  - feature101: actual docker build, compose-up health probe, image-size guard.
  - feature102: invalid email inputs and interactive delete confirmation behavior.
