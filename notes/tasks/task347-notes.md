# task347 notes

## Summary
- Added docs-level troubleshooting guidance for Feature68 CI workflows, including deterministic non-zero failure behavior and common remediation paths for missing secrets, signing failures, and publish failures.
- Added integration test `test_feature68_ci_failure_and_troubleshooting_docs` to keep workflow examples and docs guidance aligned.
- Added workflow integrity test `test_feature68_workflow_secret_env_guards` to ensure required secret/env guards remain present in `.github/workflows/kinnoo-publish.yml`.
- Kept workflow/docs command examples consistent across check/pack/publish stage references.

## Teaching Notes
- Docs are executable contracts in CI-heavy tooling: once commands/secrets are documented, lock them down with tests to prevent accidental drift.
- Testing both narrative docs and YAML workflow structure catches different failure classes: wording regressions and behavioral guardrail regressions.
- Deterministic CI failures are a feature, not a nuisance: explicit non-zero exits plus actionable messages reduce MTTR when pipelines fail.
- Add troubleshooting guidance where operators look first (README + schema docs) so on-call responders can recover without code spelunking.

## Validation
- `python3 -m pytest tests --testmon -k "test_feature68_ci_failure_and_troubleshooting_docs or test_feature68_workflow_secret_env_guards"`
