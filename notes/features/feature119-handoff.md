# Feature119 Handoff - Pre-release Feature 2 Postgres Registry DB Planning

## Scope
Feature119 defines implementation-ready planning manifests for Postgres registry DB rollout: IaC foundation, server DB runtime/schema, metadata backend cutover, migration parity gates, CLI admin workflows, testing harness, and operational readiness.

## Task Breakdown
- `task505` (human): prerequisite decisions and rollout guardrails
- `task506` (swe): Terraform Postgres module + ECS/Secrets wiring
- `task507` (swe): server DB package, 8-table schema, repositories, Alembic setup
- `task508` (swe): PostgresMetadataManager + backend-flag integration + health wiring
- `task509` (swe): JSON→Postgres backfill + parity checker + rollback gate tooling
- `task510` (swe): `kinnoo-server` DB/admin command surface
- `task511` (swe): local/CI Postgres test harness + rollback-isolated fixtures + concurrency sanity
- `task512` (swe): observability, resilience requirements, and runbooks
- `task513` (human): final cutover gate execution and sign-off

## Test Coverage Map
- `test720` validates planning prerequisites and human decision capture.
- `test721`-`test722` validate Terraform DB posture and ECS env/secret contract.
- `test723`-`test724` validate schema/repository and migration lifecycle contracts.
- `test725`-`test726` validate backend-flag parity, health checks, and outage behavior.
- `test727` validates backfill/parity/rollback gate.
- `test728` validates server DB/admin CLI surface.
- `test729`-`test730` validate Postgres harness and concurrency/pool sanity.
- `test731` validates observability/runbook contract.
- `test732` validates final human go/no-go gate.

## Sequencing Guidance
1. Complete `task505` decision gate before implementation.
2. Execute `task506` (IaC) then `task507` (server DB foundation).
3. Integrate `task508` backend flag and app health behavior.
4. Parallelize `task509`, `task510`, and `task511` after foundation stabilizes.
5. Execute `task512` runbooks/ops hardening.
6. Finish with `task513` human cutover/rollback rehearsal and approval.

## Constraints and Risk Notes
- `REGISTRY_METADATA_BACKEND` must default to `json` until parity gates pass.
- UserStore/TenantStore replacement remains gated on feature118 readiness.
- Initial rollout must preserve rollback path and avoid destructive migration posture.
- DB runtime must fail fast on startup in postgres mode when DB is unavailable.
