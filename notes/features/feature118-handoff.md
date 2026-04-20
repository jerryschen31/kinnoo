# Feature118 Handoff - Pre-release Feature 1 Kinde Auth Cutover Planning

## Scope
Feature118 decomposes pre-release feature 1 into executable human/SWE/test work for Kinde auth cutover with provider-portable architecture across server, web, CLI, identity mapping, and deployment configuration.

## Task Breakdown
- `task496` (human): prerequisite decisions + Kinde tenant/app/secrets setup
- `task497` (swe): server OIDC adapter + auth route cutover
- `task498` (swe): web redirect/callback/logout migration
- `task499` (swe): CLI login/logout/refresh migration
- `task500` (swe): internal identity mapping + publish ownership
- `task501` (swe): provider-neutral config + IaC env alignment
- `task502` (swe): legacy auth runtime retirement/compat gating
- `task503` (swe): auth portability and integration test expansion
- `task504` (human): dev smoke matrix + rollback rehearsal

## Test Coverage
- `test706`-`test716` cover feature118 AC1-AC11 end-to-end.
- Coverage includes manual prerequisite/smoke validation plus automated server/web/CLI auth and portability contract tests.

## Sequencing Guidance
1. Complete `task496` prerequisite and setup decisions first.
2. Execute `task497` server cutover baseline before web/CLI migrations.
3. Parallelize `task498` and `task499` after server baseline stabilizes.
4. Execute `task500` and `task501` next to finalize identity/config contracts.
5. Execute `task502` to retire default legacy auth runtime paths.
6. Execute `task503` automation expansion, then `task504` smoke/rollback validation.

## Release-Risk Notes
- Highest risk areas: callback/config mismatches, token refresh edge cases, and identity/tenant ownership drift.
- Mitigation: adapter boundary enforcement, fail-fast config checks, and multi-surface auth regression coverage.
