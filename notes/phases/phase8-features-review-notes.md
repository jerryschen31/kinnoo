# Phase 8 Features Review Notes

## Tech Lead Review 1

Date: 2026-04-04
Reviewer: techlead-agent
Scope: feature86-feature88 (Phase 8 client-side security hardening)

### Scope and evidence reviewed
- Phase plan baseline: `notes/phases/phase8-planning-3.md` (Phase 8 section).
- Feature/task/test manifests:
  - `FEATURES.txt` entries for feature86-feature88
  - `TASKS.txt` entries task382-task387
  - `TESTS.txt` entries test541-test546
- Implementation files:
  - `src/kinnoo/integrity.py`
  - `src/kinnoo/pack_command.py`
  - `src/kinnoo/install_command.py`
  - `src/kinnoo/cli.py`
- Feature test files:
  - `tests/test_feature_86.py`
  - `tests/test_feature_87.py`
  - `tests/test_feature_88.py`

### Commands run
- Phase 8 feature tests:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests/test_feature_86.py tests/test_feature_87.py tests/test_feature_88.py`
  - Result: PASS (6 passed)
- Full regression:
  - `/Users/jerry/.pyenv/versions/3.11.12/bin/python -m pytest tests`
  - Result: PASS (516 passed, 10 skipped)
- Credential/token pattern scan:
  - `rg -n --hidden --glob '!*.pyc' --glob '!*__pycache__*' --glob '!build/**' --glob '!.git/**' '(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*["\''][^"\''\n]{8,}["\'']'`

### Feature implementation and AC coverage assessment

#### feature86 — Embedded integrity manifest
- Status in manifests:
  - Feature: `needs-review`
  - Tasks: task382/task383 `needs-review`
- AC coverage summary:
  - AC1/AC2: covered by `tests/test_feature_86.py::test_feature86_group1` and verified in run.
  - AC3: covered by direct checks for `compute_integrity_manifest` and `verify_integrity_manifest` behavior.
  - AC4: covered by module docstring check for manifest schema/example.
  - AC5: indirectly validated by full regression pass (pack-related suites also pass).
- Result: implementation is present and behaviorally correct for ACs.

#### feature87 — Embedded signature
- Status in manifests:
  - Feature: `needs-review`
  - Tasks: task384/task385 `needs-review`
- AC coverage summary:
  - AC1/AC2: covered by signed archive generation and cryptographic verification against raw integrity bytes.
  - AC3: covered for presence of fields (`signature`, `public_key_fingerprint`, `signed_at`).
  - AC4: covered via unsigned pack path ensuring no `META-INF/signature.json`.
  - AC5: implementation reuses existing signing module; no new crypto dependency observed.
  - AC6: tests verify signed archives validate successfully.
- Result: implementation is present and AC intent is largely satisfied.

#### feature88 — Install-time integrity verification
- Status in manifests:
  - Feature: `needs-review`
  - Tasks: task386/task387 `needs-review`
- AC coverage summary:
  - AC1/AC2: covered via valid/tampered archive install checks.
  - AC3: strict mode signature enforcement covered.
  - AC4: `--skip-verify` path covered.
  - AC5: backward-compat missing-integrity path covered with warning.
  - AC6: success-path verification summary logging covered (file count + pass).
  - AC7: valid/tampered/missing-manifest/unsigned+strict/skip-verify are all covered.
- Result: implementation is present and tests passed.

### Findings (ordered by severity)

1. Medium — test depth gap for feature87 AC3 format strictness
- Current tests confirm that `signed_at` and `public_key_fingerprint` exist and are strings, but do not validate:
  - `signed_at` is ISO-8601 format.
  - fingerprint format is hex and expected length.
- Risk: malformed metadata could pass tests while violating interface expectations.

2. Medium — implementation duplication between `pack_command` and integrity module
- `src/kinnoo/pack_command.py` computes archive integrity via local helper (`_build_archive_integrity_manifest`) instead of reusing `src/kinnoo/integrity.py` primitives.
- This is not a functional bug today, but creates maintenance drift risk if manifest rules evolve.

3. Low — TESTS preconditions wording is stale for phase8 client features
- test541-test546 preconditions say "server test fixtures available" although these are CLI/client security features.
- No runtime impact; documentation clarity issue.

### Security review (sensitive tokens/credentials/passwords)
- Pattern scan produced matches mostly in:
  - test fixtures (`tests/`, `server/tests/`, `mock-server/tests/`)
  - local scripts/docs with explicit placeholder/dev-secret wording.
- No clear evidence of real production secrets introduced by feature86-feature88 changes.
- Recommendation:
  - Keep scan in CI for regression prevention.
  - Optionally tighten docs/scripts to avoid realistic-looking token literals where not needed.

### Phase 8 plan alignment check
Based on `notes/phases/phase8-planning-3.md`, Phase 8 expected features are feature86-feature88.
- All three are implemented in code and mapped to tasks/tests in manifests.
- All feature-specific tests pass.
- Full regression is green.

### Minor bug fixes made in this review
- None required for feature86-feature88.
- Rationale: no failing behavior found in feature-scoped tests or full regression related to Phase 8 tasks.

### Overall verdict
- feature86: ready for Tech Lead approval path after addressing optional medium-depth test improvements.
- feature87: functionally ready; recommend strengthening AC3 metadata format assertions before final completion sign-off.
- feature88: ready for Tech Lead approval path.

### Recommended follow-up improvements (non-blocking)
1. Add strict format assertions in `tests/test_feature_87.py` for `signed_at` (ISO 8601) and fingerprint hex shape.
2. Refactor `pack_command` to reuse integrity module logic where practical, or explicitly document why archive-level helper is intentionally separate.
3. Clean up stale test precondition text in TESTS entries test541-test546.
