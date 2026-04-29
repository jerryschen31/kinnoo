# Feature118 Handoff - Pre-release Feature 1 Kinde Auth Cutover Planning

## Scope
Feature118 decomposes pre-release feature 1 into executable human/SWE/test work for Kinde auth cutover with provider-portable architecture across server, web, CLI, identity mapping, and deployment configuration.

## Two-App Kinde Topology (Resolved per Issue #350)
- **Kinnoo Web Dev** (Backend/Python): Confidential client for browser-based web login. Server mediates auth flow with client secret.
- **Kinnoo CLI Dev** (Frontend/Native, Other native): Public client with PKCE for `kinnoo login`. CLI uses dynamic-port loopback callback (preferred 8765, fallback 8766/8767, then OS-assigned). No client secret at runtime.
- Both apps share the same Kinde tenant, issuer, and JWKS — server validates tokens from both.
- See notes/kinde-auth-setup-followup.md for full decision rationale.

## Task Breakdown
- `task496` (human): prerequisite decisions + dual Kinde app setup (Web Dev + CLI Dev)
- `task497` (swe): server OIDC adapter + auth route cutover (uses Web Dev client, validates tokens from both apps)
- `task498` (swe): web redirect/callback/logout migration (uses Web Dev client)
- `task499` (swe): CLI login/logout/refresh migration (uses CLI Dev public client, PKCE, dynamic-port loopback)
- `task500` (swe): internal identity mapping + publish ownership (works across both login paths)
- `task501` (swe): provider-neutral config with dual client IDs + IaC env alignment
- `task502` (swe): legacy auth runtime retirement/compat gating
- `task503` (swe): auth portability and integration test expansion (covers both Kinde apps)
- `task504` (human): dev smoke matrix across both login paths + rollback rehearsal

## Test Coverage
- `test706`-`test716` cover feature118 AC1-AC11 end-to-end.
- Coverage includes manual prerequisite/smoke validation plus automated server/web/CLI auth and portability contract tests.
- Tests verify token validation, identity mapping, and ownership linkage work correctly for tokens from both Kinde apps.

## Sequencing Guidance
1. Complete `task496` prerequisite and dual-app setup decisions first.
2. Execute `task497` server cutover baseline before web/CLI migrations.
3. Parallelize `task498` (web, Web Dev client) and `task499` (CLI, CLI Dev client) after server baseline stabilizes.
4. Execute `task500` and `task501` next to finalize identity/config contracts with dual client ID support.
5. Execute `task502` to retire default legacy auth runtime paths.
6. Execute `task503` automation expansion (both apps), then `task504` smoke/rollback validation.

## Release-Risk Notes
- Highest risk areas: callback/config mismatches (now split across two apps), token refresh edge cases, and identity/tenant ownership drift.
- Mitigation: adapter boundary enforcement, fail-fast config checks for dual client IDs, and multi-surface auth regression coverage.
