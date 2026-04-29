# Operator Launch-Week Timeline (Phase-Ordered)

This is a compact, single-sequence checklist for operator-owned launch work.
It is derived from manual tasks task441-task447 and manual/regression checks test600-test606.

## How to use

- Run items top to bottom.
- Do not skip a gate check.
- Mark each item complete with date, owner, and artifact link.

## Phase 13: Public + Packaging Readiness

### 1) Public repository final scrub and signoff

- Task: task447
- Test/Script: test600 -> scripts/ops/public_repo_readiness_check.sh
- Gate to pass:
  - Secret scan clean
  - Internal-only notes/content removed or excluded
  - CONTRIBUTING/CODE_OF_CONDUCT/templates reviewed
  - Signoff recorded in docs/public-release-signoff.md

### 2) PyPI trusted publisher setup (OIDC)

- Task: task443
- Test/Script: test601 -> scripts/ops/check_pypi_trusted_publisher.sh
- Gate to pass:
  - Trusted publisher configured in PyPI
  - Release workflow mapping is correct
  - OIDC auth succeeds without static token

## Phase 12: Infrastructure Foundations

### 3) Terraform state bootstrap apply

- Task: task441
- Test/Script: test602 -> scripts/ops/check_terraform_state_bootstrap.sh
- Gate to pass:
  - Backend S3 bucket + DynamoDB lock table created
  - Backend details captured in docs/iac-operator-runbook.md

### 4) Cloudflare DNS and ACM validation setup

- Task: task442
- Test/Script: test603 -> scripts/ops/check_cloudflare_dns_setup.sh
- Gate to pass:
  - dev.kinnoo.ai resolves correctly
  - dev-api.kinnoo.ai resolves correctly
  - ACM DNS validation records present

## Phase 14: Beta Operations Workflow

### 5) Forgot-password operator drill

- Task: task444
- Test/Script: test604 -> scripts/ops/check_forgot_password_runbook.sh
- Gate to pass:
  - Forgot-password request receives expected generic response
  - SNS alert reaches operator mailbox
  - CLI reset works and user can log in with reset credentials

## Phase 15: Launch Validation

### 6) Registry seeding execution (signed, multi-framework)

- Task: task445
- Test/Script: test605 -> scripts/ops/check_registry_seeding.sh
- Gate to pass:
  - >=3 agents published across frameworks
  - >=1 agent signed
  - Search/install/run validated for all seeded agents
  - Evidence captured in outputs/registry-seeding/

### 7) Final launch checklist run and go/no-go

- Task: task446
- Test/Script: test606 -> scripts/ops/check_launch_readiness.sh
- Gate to pass:
  - All launch checklist items executed with evidence
  - Critical smoke checks rerun
  - Go/no-go decision recorded with timestamp and owner

## One-page execution order

1. task447 -> test600
2. task443 -> test601
3. task441 -> test602
4. task442 -> test603
5. task444 -> test604
6. task445 -> test605
7. task446 -> test606

## Suggested launch-week cadence

- Early week (Mon-Tue): task447, task443
- Mid week (Tue-Thu): task441, task442, task444
- Late week (Thu-Fri): task445
- Launch day: task446

## Evidence checklist (copy/paste)

- [ ] task447 complete (link):
- [ ] task443 complete (link):
- [ ] task441 complete (link):
- [ ] task442 complete (link):
- [ ] task444 complete (link):
- [ ] task445 complete (link):
- [ ] task446 complete (link):
- [ ] final go/no-go owner:
- [ ] final go/no-go timestamp:
