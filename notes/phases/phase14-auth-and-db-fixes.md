# Phase 14 Auth and DB Fixes

Date: 2026-04-20
Scope: Auth/OIDC stabilization, Postgres deployment readiness, DB secret correctness, hosted CLI login interoperability
Commits referenced: 5b67947, 3a58cee, b19dcee

## Executive Summary
This phase closed a multi-step chain of deployment and runtime issues across CLI auth, server OIDC validation, Terraform Postgres defaults, ECS runtime wiring, and secret formatting. The end state achieved in this phase:
- Hosted CLI login works with Kinde in free-plan-compatible mode.
- Registry operations list, search, and publish work after login.
- Postgres is deployed and migrations succeed from ECS runtime.
- REGISTRY_DATABASE_URL secret generation is safe for rotated passwords containing reserved URL characters.
- A reusable shell utility exists for refreshing DB URL secret after RDS password rotation.
- A reusable shell utility exists for loading hosted auth environment variables from AWS Secrets Manager.

## User-Visible Problems Encountered
- Hosted CLI login initially failed with invalid_scope due to offline_access.
- Hosted CLI login later succeeded but registry calls returned 401 token audience invalid.
- After audience fixes, registry calls returned 403 missing required scope registry:read.
- Requesting registry:read directly from Kinde produced invalid_scope due to client plan/capability constraints.
- DB migration failed with Database connectivity check failed even though network path to RDS was open.
- RDS password contained reserved URL characters that broke a raw connection URL.
- ECS runtime lacked db CLI surface at one point due to stale image mismatch.

## Commit-by-Commit Details

## Commit 5b67947
Title: fixed kinnoo login auth flow
Files:
- src/kinnoo/auth_command.py
- tests/client_cli_registry/test_feature118_cli_auth.py

What changed:
- Updated callback port order from dynamic/fallback style to fixed deterministic ports.
- Removed offline_access from hosted CLI authorization scope.
- Added tenant slug source strategy support:
  - Default prefers email-derived slug for stable human-readable tenant slug.
  - Optional env-driven override to prefer org_code.
- Added tenant slug helper normalization logic.
- Added tests for:
  - Hosted scope not containing offline_access.
  - Tenant slug source default behavior.
  - Tenant slug source org_code override behavior.

Why it mattered:
- Fixed Kinde invalid_scope failures tied to offline_access.
- Reduced tenant context surprise in CLI by making slug derivation strategy explicit and configurable.

## Commit 3a58cee
Title: postgres database now deployed
Files:
- iac/environments/dev/terraform.tfvars
- iac/modules/lambda-security-check/variables.tf
- iac/modules/rds-postgres/main.tf
- scripts/ops/refresh_registry_database_url_secret.sh

What changed:
- Set dev metadata backend target to postgres in dev tfvars.
- Kept DB pool values in tfvars.
- Moved lambda security-check image default/tag handling toward latest for deployment simplicity.
- Adjusted RDS non-prod retention behavior to free-tier-compatible value.
- Pinned RDS engine version to a region-supported patch version.
- Added reusable script scripts/ops/refresh_registry_database_url_secret.sh to:
  - Read RDS managed master secret.
  - URL-encode username/password.
  - Build a safe SQLAlchemy URL.
  - Write JSON-keyed REGISTRY_DATABASE_URL secret expected by ECS secret injection.
  - Print only redacted URL shape.

Why it mattered:
- Unblocked Terraform apply failures tied to non-prod backup retention and unsupported engine patch.
- Removed manual/unsafe DB URL creation workflows during password rotation.

## Commit b19dcee
Title: kinnoo login auth, list, search, publish now all work. Still need to fix tenant slug to be same as login through web UI
Files:
- scripts/load_kinnoo_auth_env.sh
- server/auth/oidc.py
- src/kinnoo/auth_command.py

What changed:
- Added scripts/load_kinnoo_auth_env.sh to load hosted OIDC env config from AWS Secrets Manager.
- Added robust JSON secret value extraction in loader script.
- Consolidated hosted login scope constant in CLI auth command.
- Added OIDC scope compatibility mapping in server token service:
  - If token contains only openid/profile/email and no registry scopes,
  - server can append registry:read and registry:publish claims internally when compatibility is enabled.
- Added compatibility flag AUTH_ENABLE_OIDC_SCOPE_COMPAT (defaults enabled in this implementation path).

Why it mattered:
- Enabled non-paid Kinde scope path while preserving registry authorization behavior.
- Removed fragile per-developer manual export steps.

## Root Cause Analyses and Responses Provided During This Phase

## 1) Kinde invalid_scope for offline_access
Root cause:
- Web/CLI client configuration did not allow requested offline_access scope.

Response provided:
- Remove offline_access from hosted login request.
- Keep base scopes openid profile email.

Outcome:
- Hosted login could complete again.

## 2) 401 token audience invalid
Root cause:
- CLI token audience claim did not match server expected AUTH_AUDIENCE.
- In observed case, token aud was empty list while server expected https://dev-api.kinnoo.ai.

Response provided:
- Verify token aud claim and server AUTH_AUDIENCE in ECS runtime.
- Load AUTH_AUDIENCE and related OIDC env vars from Secrets Manager.
- Re-login to mint fresh token.

Outcome:
- Audience mismatch diagnosis confirmed and corrected.

## 3) 403 missing required scope registry:read
Root cause:
- Token had OIDC identity scopes but lacked registry API scopes.

Response provided:
- Attempted strict scope request path first.
- After Kinde plan limitation surfaced, introduced server compatibility mapping for free-plan operation.

Outcome:
- list/search/publish operations restored without paid Kinde API scope feature.

## 4) invalid_scope for registry:read requested scope
Root cause:
- OAuth client not allowed to request custom API scopes in current Kinde setup/plan.

Response provided:
- Avoid hard dependency on paid custom scopes.
- Keep hosted login requesting base identity scopes only.
- Add server-side compatibility expansion to registry scopes under explicit compatibility control.

Outcome:
- Functional registry operations retained with Kinde auth, no mandatory paid plan.

## 5) DB connectivity check failed during migration
Root cause:
- Sync SQLAlchemy connectivity probe executed against URL scheme not aligned for sync path, while TCP connectivity to RDS was healthy.

Response provided:
- Diagnose from running ECS task:
  - validate env URL shape
  - validate TCP reachability to RDS host:5432
  - verify scheme mismatch hypothesis
- Regenerate secret using sync-compatible scheme and redeploy ECS.

Outcome:
- db migrate succeeded from ECS runtime.

## 6) Password characters breaking DB URL
Root cause:
- Reserved characters in RDS-generated password require percent-encoding in URL userinfo component.

Response provided:
- Implemented URL-encoding in secret refresh script.
- Wrote secret as JSON key REGISTRY_DATABASE_URL for ECS JSON-key extraction wiring.

Outcome:
- Reliable DB URL generation regardless of rotated password content.

## Operational Commands and Playbooks Shared in This Phase
- Rebuild/push/redeploy server image:
  - scripts/ops/rebuild_push_server_and_redeploy_ecs.sh
- Refresh DB URL secret after password rotation:
  - scripts/ops/refresh_registry_database_url_secret.sh <db_instance_identifier> [environment] [region] [project] [db_name]
- Load OIDC env vars locally from Secrets Manager:
  - source scripts/load_kinnoo_auth_env.sh
  - kinnoo_load_auth_env dev us-west-2 kinnoo
  - or eval "$(scripts/load_kinnoo_auth_env.sh dev us-west-2 kinnoo)"
- Force ECS rollout after secret/config changes:
  - aws ecs update-service --region us-west-2 --cluster kinnoo-dev-cluster --service kinnoo-dev-service --force-new-deployment

## Terraform and Runtime Guidance Given
- Non-secret DB runtime config belongs in tfvars and flows through ECS env injection.
- Secret DB URL belongs in Secrets Manager and should be consumed via ECS secret mapping.
- App-to-RDS network path must allow ECS SG to DB SG on tcp/5432.
- In postgres metadata mode, migrations are still required even for fresh DB (schema initialization).

## Validation Evidence Captured During Phase
- Focused CLI auth regression suite passed after scope/tenant flow updates:
  - tests/client_cli_registry/test_feature118_cli_auth.py
- ECS runtime checks confirmed:
  - URL env present in task
  - TCP connectivity to RDS host:5432
  - post-fix migration success message Database migration completed: head
- Secret regeneration checks confirmed:
  - URL percent encoding present where needed
  - redacted URL shape valid

## Remaining Follow-up Notes
- Tenant slug parity between CLI and web login remains called out in commit message as future alignment work.
- When paid custom API scopes are adopted later, compatibility mapping can be disabled and strict registry scope validation can be enforced end-to-end.
- Consider implementing public auth config discovery endpoint for pip-installed users to avoid local env bootstrapping.

## Response Notes Summary (What was communicated to unblock progress)
- Clarified where to set DB non-secret runtime values versus where to store secret DB URL.
- Clarified why callback/login could succeed while API calls still fail (audience/scope are separate checks).
- Clarified why browser did not prompt email again (existing Kinde session reuse).
- Clarified why task definition churn can appear as volume replacement noise despite same EFS wiring.
- Clarified that fresh Postgres cutover without JSON backfill is valid if user accepts non-parity for prior S3-only metadata.
- Clarified free-plan Kinde workaround path to avoid mandatory paid scope management.

## File and Change Cross-Reference
- Commit 5b67947: auth flow and tenant slug strategy hardening.
- Commit 3a58cee: Postgres deployment readiness and DB URL secret automation.
- Commit b19dcee: auth env loader and OIDC scope compatibility path for practical production use.
