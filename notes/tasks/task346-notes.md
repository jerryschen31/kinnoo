# task346 notes

## Summary
- Added reference GitHub Actions workflow at `.github/workflows/kinnoo-publish.yml` covering install, preflight check, pack, and remote publish stages.
- Defined CI environment and secret contract in workflow/docs: `KINNOO_REGISTRY_URL`, `KINNOO_REGISTRY_TOKEN`, `KINNOO_TENANT_SLUG`, and `KINNOO_CI_STRICT_MODE`.
- Added docs updates in `README.md` and `docs/manifest-schema-reference.md` describing stage ordering, strict-mode compatibility, and fail-fast/non-zero behavior.
- Added docs changelog entry for Feature68 rollout.
- Added regression test `test_feature68_workflow_contract_and_envs` to assert workflow stage and env contract consistency.

## Teaching Notes
- CI contracts are product interfaces: treat required secrets/env vars like API inputs and lock them with tests so drift is caught quickly.
- Workflow fail-fast behavior (`set -euo pipefail`) is key for deterministic automation; silent continuation creates hard-to-debug partial publishes.
- Keep docs and workflow in the same change set so operators can follow a single source of truth for setup and troubleshooting.
- Parse-and-assert tests for workflow YAML are low-cost guardrails that prevent accidental pipeline regressions.

## Validation
- `python3 -m pytest tests --testmon -k test_feature68_workflow_contract_and_envs`
