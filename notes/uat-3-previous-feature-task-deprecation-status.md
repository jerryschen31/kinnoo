# UAT 3 Previous Feature/Task Deprecation Status

Date: 2026-04-23
Scope: FEATURES.txt and TASKS.txt entries not in completed / paused / deprecated status.
Method: Manifest status scan + current codebase trajectory review (notably UAT 3 auth and CLI updates) to estimate deprecation likelihood.

## 1) Active Feature IDs (not completed / paused / deprecated)
feature61, feature86, feature87, feature88, feature89, feature90, feature91, feature92, feature93, feature94, feature95, feature96, feature97, feature98, feature99, feature100, feature101, feature104, feature111, feature112, feature115, feature120

## 2) Active Task IDs (not completed / paused / deprecated)
task332, task333, task334, task335, task336, task337, task338, task339, task340, task341, task382, task383, task384, task385, task386, task387, task388, task389, task390, task391, task392, task393, task394, task395, task396, task397, task398, task399, task400, task401, task402, task403, task404, task405, task406, task407, task408, task409, task410, task411, task412, task413, task414, task415, task416, task417, task418, task419, task420, task421, task422, task423, task424, task425, task426, task427, task428, task429, task430, task431, task432, task433, task434, task435, task436, task437, task438, task439, task440, task442, task443, task444, task445, task446, task447, task448, task449, task450, task451, task452, task453, task454, task455, task456, task457, task458, task459, task460, task461, task462, task479, task480, task481, task482, task483, task496, task497, task498, task499, task500, task501, task502, task503, task504, task505, task506, task507, task508, task509, task510, task511, task512, task513, task514, task515

## 3) Task-by-Task Deprecation Likelihood

### A. Likely stale due to already-deprecated OpenClaw bridge strategy (high deprecation risk)

task334: "Feature62 openclaw-skill schema and validator extension"
- Feature62 is already deprecated and replaced by Phase 7 wrapper model, so this active task is likely obsolete and should likely be deprecated (96%).

task335: "Feature62 schema fixture coverage and migration guidance"
- This supports a deprecated feature branch (feature62), so it is likely no longer strategic and should likely be deprecated (95%).

task336: "Feature63 ClawHub mirror storage with clawhub tenant ownership model"
- Feature63 is deprecated in favor of direct wrapper flows, making this mirror-focused task likely obsolete and likely deprecatable (97%).

task337: "Feature63 mirror attribution UX and query behavior"
- Mirror attribution work ties to deprecated feature63 path, so this should likely be deprecated unless explicitly resurrected (95%).

task338: "Feature64 kinnoo import source clawhub command path"
- Feature64 was deprecated in favor of direct workspace import wrappers, so this bridge import task is likely obsolete (96%).

task339: "Feature64 import hinting and unresolved guidance"
- This is downstream of deprecated bridge import flow and likely no longer aligned with current architecture (94%).

task340: "Feature65 delegated OpenClaw install runtime integration"
- Feature65 deprecated in favor of feature80 wrapper/extract path, so this delegated bridge task likely should be deprecated (96%).

task341: "Feature65 delegated install failure-mode handling and tests"
- Since the parent install bridge strategy is deprecated, this follow-on hardening task is likely obsolete (94%).

### B. Active auth and UAT tasks (low deprecation risk)

task332: "Feature61 login/logout CLI commands and auth state persistence"
- Recent UAT/auth changes reinforce this direction (hosted discovery, fail-fast fallback behavior), so this remains relevant and should not be deprecated (12%).

task333: "Feature61 login/logout tests and operator documentation"
- Supporting tests/docs remain required for feature61 closure and still align with current auth flows (10%).

task449: "Login and logout CLI hardening"
- This task directly tightens the current auth model and no-fallback remote behavior, so it remains important and should not be deprecated (15%).

task514: "feature120 UAT3 install/fetch selector and verification-sidecar fixes"
- This is the core UAT3 implementation lane and remains current with recent code changes (5%).

task515: "hosted auth discovery via registry config endpoint"
- This was actively worked in UAT3 and remains central to current auth architecture; not a deprecation candidate (5%).

### C. Security hardening implementation tasks in needs-review (generally low deprecation risk)

task382: "Create integrity.py module and embed SHA-256 manifest in .kno archives"
- Integrity embedding remains aligned with current security roadmap and appears additive, not superseded (14%).

task383: "Document integrity manifest format and verify pack integration"
- Still required for feature86 completeness and regression confidence; low deprecation risk (12%).

task384: "Add Ed25519 signing to .kno archives via --sign flag"
- Signature pipeline remains core to trust posture and is not contradicted by UAT3 changes (12%).

task385: "Verify signature integration and unsigned archive backward compat"
- Backward-compat safety remains necessary; no indication this direction is obsolete (10%).

task386: "Add install-time integrity and signature verification (--strict, --skip-verify)"
- This is consistent with ongoing trust/verification direction and should remain active (10%).

task387: "Handle missing manifests, tampered files, and backward compat in install"
- Defensive install behavior remains relevant and not superseded by UAT3 fixes (11%).

task388: "Add JSON logging, CORS, and health/ready endpoints to server"
- Production-readiness requirements remain valid; no architectural conflict observed (13%).

task389: "Harden Uvicorn config and enforce secret validation in production mode"
- Operational hardening remains aligned with deployment goals and should remain active (12%).

task390: "Add server-side upload validation (size, zip, manifest fields)"
- Upload validation remains strategically necessary and still fits current codebase trajectory (12%).

task391: "Enforce integrity.json validation on upload and return JSON errors"
- Continues feature90 hardening and matches current security expectations (12%).

task392: "Implement configurable per-endpoint and per-tenant rate limiting"
- Still needed for abuse protection and not replaced by other work (13%).

task393: "Add X-RateLimit-* and Retry-After headers to all responses"
- This remains a standard completion item for rate limiting and should stay active (11%).

### D. Documentation and release-prep tasks in needs-review (low-to-moderate deprecation risk)

task394: "Create kinnoo.yaml spec doc with field reference table"
- Still needed for public/beta readiness and manifest clarity; low deprecation risk (14%).

task395: "Add framework examples and version/compat notes to spec doc"
- Complementary doc completion task remains relevant (13%).

task396: "Create CLI reference doc for client commands (init through uninstall)"
- CLI docs remain required and should not be deprecated (12%).

task397: "Add server CLI commands and cross-references to CLI reference"
- Still relevant for operator workflows and consistency (12%).

task398: "Create security model doc with threat model and signing architecture"
- Security documentation remains essential for release and review (11%).

task399: "Document auth flow and cross-reference from README"
- Auth flow docs are still needed post-UAT auth changes (10%).

task400: "Create getting-started guide with end-to-end agent walkthrough"
- Still a standard release artifact; no sign of obsolescence (14%).

task401: "Create registry guide with publish/install workflows and expected output"
- Registry guide remains needed and aligned with current product direction (13%).

task402: "Rewrite README for beta with badges and quick-start"
- README modernization remains relevant for public-facing readiness (14%).

task403: "Create supported-agents.md with framework compatibility matrix"
- Compatibility matrix remains useful and not superseded (13%).

task404: "Audit repo for secrets and create CONTRIBUTING.md, CODE_OF_CONDUCT.md"
- Public release hygiene work remains necessary and should not be deprecated (10%).

task405: "Create issue/PR templates and verify .gitignore coverage"
- Repository governance setup remains relevant for launch (10%).

task406: "Create CI and backend deploy GitHub Actions workflows"
- CI/CD setup remains a core release requirement; not obsolete (12%).

task407: "Create frontend deploy and Terraform plan/apply workflows with OIDC"
- OIDC-based deploy workflow remains current best practice and still needed (12%).

task408: "Validate pyproject.toml metadata and configure trusted publisher"
- Packaging/publishing metadata and trusted publisher flow remain required (11%).

task409: "Create pypi-publish.yml workflow triggered on push to master"
- Still relevant for release automation unless release strategy changed explicitly (13%).

### E. Auth/admin/infra tasks in needs-review (mostly low deprecation risk)

task410: "Implement account lockout after 5 failed logins with 15-min cooldown"
- Security hardening requirement still stands and is not superseded by UAT3 changes (12%).

task411: "Implement password policy enforcement with specific guidance messages"
- Password policy work remains current and should not be deprecated (12%).

task412: "Implement JWT token blacklist on logout with automatic pruning"
- Token revocation remains valid and useful in the current auth model (13%).

task413: "Create multi-stage production Dockerfile with non-root user and healthcheck"
- Container hardening remains essential for deployment and is not obsolete (11%).

task414: "Create docker-compose.yml for local dev and verify container startup"
- Local ops reproducibility remains relevant; low deprecation risk (12%).

task415: "Implement user management CLI commands (create, list, reset-password, unlock, delete)"
- Admin CLI utilities remain aligned with operator workflows (12%).

task416: "Implement invite token CLI commands (create, list) with input validation"
- Invite-only beta operations still reference this flow, so not a deprecation candidate (14%).

task417: "Create iac/ project structure with versions.tf, providers.tf, and state bootstrap"
- IaC foundation remains relevant and already partially operational; low deprecation risk (10%).

task418: "Create VPC module with public subnets, security groups, and S3 endpoint"
- Core infra module remains aligned with deployment direction (11%).

task419: "Create S3 registry module with encryption, Object Lock, and versioning"
- Storage security controls remain current and should stay active (10%).

task420: "Create IAM roles module (ECS task, execution, GitHub OIDC)"
- IAM/OIDC module remains central to CI and runtime security posture (10%).

task421: "Create Secrets Manager module for JWT, session, and admin secrets"
- Secret management remains necessary and not superseded (10%).

task422: "Create ECR repository and ALB modules with HTTPS/ACM"
- Compute/network deployment modules remain active requirements (10%).

task423: "Create ECS Fargate cluster, task definition, and service"
- ECS service provisioning remains relevant and not deprecated (11%).

task424: "Create EFS module with mount targets and verify terraform validate"
- Persistent storage module remains part of current infra baseline (12%).

task425: "Create Cloudflare DNS module for dev.kinnoo.ai and dev-api.kinnoo.ai"
- DNS module remains relevant; blockers were operational, not strategic (12%).

task426: "Add ACM validation CNAME records and Cloudflare API token config"
- Certificate validation wiring remains necessary and not obsolete (11%).

task427: "Create CloudWatch log group and alarm modules (5xx, unhealthy, CPU)"
- Monitoring controls remain needed for production readiness (12%).

task428: "Create SNS topics for alerts and password reset notifications"
- Alerting integrations remain relevant operationally (12%).

task429: "Add invite token validation to registration endpoint"
- Invite-only enforcement is still reflected in roadmap, so low deprecation likelihood (16%).

task430: "Add invite token field to web registration and handle race conditions"
- Dependent UX/backend piece still fits invite-only beta direction (16%).

task431: "Add forgot-password endpoint with SNS notification to operator"
- Manual operator reset flow still appears active in plans and not superseded (17%).

### F. Not-started operational rollout tasks (generally defer, not deprecate)

task432: "Add forgot-password web page with rate limiting"
- Not started but still required to complete feature109 intent; likely defer, not deprecate (18%).

task435: "Create e2e smoke test script with parameterized registry URL and credentials"
- Still needed for release validation; no evidence it is obsolete (15%).

task436: "Add cleanup, CI integration, and per-step timing to smoke test"
- Follows directly from task435 and remains relevant once e2e script exists (15%).

task437: "Publish 3+ agents covering different frameworks to the registry"
- Operational seeding remains useful for beta launch and not superseded (18%).

task438: "Verify searchability, installability, and document seeding process"
- Still relevant as rollout verification/documentation work (17%).

task439: "Create launch checklist doc with Infrastructure, Security, CI/CD sections"
- Launch checklist remains a standard go-live artifact, not a deprecation candidate (14%).

task440: "Add User Onboarding walkthrough and make checklist actionable for operator"
- Still relevant as completion of launch checklist feature (14%).

task442: "Configure Cloudflare credentials and complete live DNS validation"
- Operational blocker task remains necessary for environment readiness (20%).

task443: "Configure PyPI trusted publisher (OIDC) for release workflow"
- Still needed for secure release pipeline and not superseded (15%).

task444: "Run operator forgot-password drill and verify reset runbook"
- Operational drill remains valid once forgot-password flow is finalized (18%).

task445: "Execute registry seeding runbook with signed multi-framework agents"
- Remains relevant for launch readiness and trust validation (17%).

task446: "Execute launch-day checklist and record go/no-go decision"
- Final launch gate remains relevant by design (12%).

task447: "Run final public-repo scrub and explicit operator release signoff"
- Public release compliance step remains required and not obsolete (12%).

task448: "Resolve dev infra blockers (Cloudflare 1014 + ECS/ECR readiness)"
- Still directly relevant to dev environment reliability; should not be deprecated (20%).

task504: "feature118 dev cutover smoke validation and rollback rehearsal"
- Still useful as final operational cutover gate, though some portions may already have been executed ad hoc (35%).

task505: "feature119 operator prerequisite decisions and rollout guardrails"
- Still relevant for controlled Postgres rollout governance; likely defer rather than deprecate (28%).

task513: "feature119 human cutover gate execution and final approval"
- Still valid as human go/no-go for DB cutover; not obviously obsolete (26%).

### G. Feature115 residual needs-review tasks (mostly still relevant, some medium risk of partial supersession)

task450: "kinnoo test hardening"
- Still relevant and independent of UAT3 auth changes; appears unfinished rather than obsolete (18%).

task451: "Fix remote install latest resolution and download URL handling"
- This fix aligns with current remote registry behavior and should remain active for review closure (10%).

task452: "Fix publish framework requirement and JS/TS runtime language handling"
- Still aligned with current architecture; no sign this issue fix should be deprecated (10%).

task453: "CLI top-level help - version, commit hash, and icon"
- Cosmetic/UX hardening still valid; low deprecation risk (20%).

task454: "init - framework as required positional argument"
- Still relevant unless product direction reverted to option-based framework selection (22%).

task455: "init - interactive wizard when no arguments"
- Wizard UX remains aligned with discoverability goals; low deprecation risk (18%).

task456: "init - change default python entrypoint to main.py"
- Could conflict if later conventions changed back, but no clear superseding evidence now (30%).

task457: "init - complete template with folders and --minimal flag"
- Template-mode split remains useful and likely still relevant (18%).

task458: "init - README.md template improvements"
- Documentation template improvements remain relevant and low risk to keep (15%).

task459: "init - language-specific .gitignore templates"
- Still relevant and unlikely obsolete unless template architecture changed fundamentally (20%).

task460: "pack - ignore data/ by default and add --include/--exclude"
- This behavior remains broadly useful and not contradicted by UAT3 changes (15%).

task461: "pack - --preflight dry-run"
- Still relevant as operator safety workflow and likely not obsolete (14%).

task462: "pack - help text updates and default patch bump"
- Help/bump refinements remain relevant though wording may need minor refresh; low deprecation risk (24%).

task479: "Registry UI - inline security icons in Name column"
- Still consistent with current trust UX direction; any UI tweaks are evolution, not deprecation (22%).

task480: "Registry - server-side security check script"
- Core security signal generation remains relevant for registry trust model (15%).

task481: "Registry - update security column and persist check report"
- Persistence/reporting layer remains aligned with security tab and icon UX goals (15%).

task482: "Registry - containerized Lambda for server-side checks"
- Execution substrate may evolve, but async/server-side check architecture still seems relevant (35%).

task483: "Registry UI - Security tab in selected-agent details"
- Security tab remains aligned with transparency goals and not obsolete (18%).

### H. Feature118/119 planning-manifest tasks left active after feature completion (medium-high deprecation risk)

task496: "feature118 prerequisite decisions and dual Kinde app setup execution"
- Most of this planning/setup appears already enacted through subsequent auth changes, so this task likely should be deprecated or marked completed retroactively (78%).

task497: "feature118 server OIDC auth adapter and route cutover"
- The server auth cutover appears materially implemented; as a planning-task artifact it is likely stale (82%).

task498: "feature118 web auth migration to Kinde-hosted redirects"
- If web auth path is already migrated, this planning task should likely be deprecated/closed to avoid duplicate tracking (80%).

task499: "feature118 CLI login/logout/refresh flow migration"
- CLI auth migration has active code and UAT3 fixes; this planning task likely represents completed/superseded work (82%).

task500: "feature118 internal identity mapping and publish ownership linkage"
- Likely partially implemented during auth cutover; as a manifest planning item this is probably stale (74%).

task501: "feature118 provider-neutral auth config and IaC env alignment"
- Recent auth/env refinements suggest this has moved forward; the task likely needs closure or deprecation as planning residue (72%).

task502: "feature118 legacy auth runtime retirement and compatibility gating"
- Legacy-auth gating has been actively changed; this planning task appears largely superseded by actual implementation (76%).

task503: "feature118 auth portability and integration test expansion"
- Some test expansion may remain, but as feature-level planning residue this likely needs consolidation into concrete follow-up tasks (68%).

task506: "feature119 phase13.1 terraform postgres foundation and ecs wiring"
- If feature119 is considered complete at manifest level, this active task likely reflects stale decomposition and should be reconciled (70%).

task507: "feature119 phase13.2 server database package schema and migrations"
- Likely still conceptually relevant, but as a planning-manifest remnant under completed feature it has high risk of being stale (72%).

task508: "feature119 phase13.2 metadata backend integration and health wiring"
- Same mismatch pattern (completed feature, active task) suggests this should be reconciled, possibly deprecated/replaced (70%).

task509: "feature119 phase13.3 json-to-postgres migration parity and rollback gates"
- May still be needed operationally, but tracking likely needs restructuring; medium-high deprecation risk in current manifest form (65%).

task510: "feature119 server db/admin command surface for postgres operations"
- Could still be needed but appears out-of-sync with feature completion status; likely requires consolidation (66%).

task511: "feature119 postgres test harness local-dev and ci integration"
- Work is still valuable but task bookkeeping likely stale relative to feature status (64%).

task512: "feature119 observability resilience runbooks and scalability controls"
- Still relevant in substance, but this active planning task likely needs remapping to current phase/features (63%).

## 4) Feature-Level Deprecation Likelihood (based on active task set)

feature61: "kinnoo login and logout commands"
- Active tasks align with current UAT3 auth trajectory and hardening direction; this feature should remain active, not deprecated (15%).

feature86: "Embedded integrity manifest (META-INF/integrity.json)"
- Active implementation/review tasks remain aligned with trust roadmap and not superseded (12%).

feature87: "Embedded signature (META-INF/signature.json)"
- Signature embedding remains strategically aligned and should stay active (12%).

feature88: "Install-time integrity verification"
- Install verification remains core to supply-chain trust and not deprecated (11%).

feature89: "Production server configuration and deployment hardening"
- Production hardening tasks remain relevant and unsuperseded (13%).

feature90: "Server-side upload validation and integrity enforcement"
- Upload validation remains current security requirement and should stay active (12%).

feature91: "Production-grade rate limiting and abuse protections"
- Abuse controls remain relevant and still needed (12%).

feature92: "kinnoo.yaml specification document"
- Documentation gap remains meaningful and feature should remain active (14%).

feature93: "CLI command reference document"
- Still needed for public/operator usability; low deprecation likelihood (13%).

feature94: "Security model document"
- Security documentation remains a required release artifact (12%).

feature95: "Getting started guide and registry guide"
- Still relevant for onboarding and launch readiness (14%).

feature96: "README rewrite and supported agents document"
- Remains relevant for beta/public readiness and not superseded (14%).

feature97: "Public GitHub repository preparation"
- Release hygiene scope remains valid; not a deprecation candidate (12%).

feature98: "GitHub Actions CI/CD pipeline"
- CI/CD hardening remains relevant unless replaced by another pipeline strategy (16%).

feature99: "PyPI package publishing configuration"
- Still relevant for distribution and release automation (14%).

feature100: "Auth hardening — lockout, password policy, token blacklist"
- In-progress security hardening remains current and should stay active (10%).

feature101: "Production Dockerfile and docker-compose"
- Containerization work remains relevant and unsuperseded (12%).

feature104: "Terraform storage and security (S3, IAM, Secrets Manager)"
- Core IaC security modules remain relevant and should stay active (10%).

feature111: "End-to-end smoke test script"
- Not started but still a key launch gate; likely defer, not deprecate (16%).

feature112: "Registry seeding and validation"
- Not started operational feature remains useful for beta readiness (18%).

feature115: "UAT Part 1 - CLI hardening"
- Large portions are done; remaining tasks appear mostly valid with limited supersession risk, so feature should not be deprecated (28%).

feature120: "UAT round 3 testing and bug fixes"
- This is the current active UAT feature with recent direct implementation activity; should definitely remain active (5%).

## Summary View

Likely deprecate now (high confidence): task334-task341.
Likely reconcile/close or split (planning residue): task496-task503, task506-task512.
Keep active (most others): security hardening, docs, infra, UAT3, and release-gate tasks.
