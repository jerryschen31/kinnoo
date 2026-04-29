# Feature 113 — SWE Handoff: Launch Readiness Checklist

## Context
Create a comprehensive go/no-go checklist for beta launch. Jerry follows this step by step on launch day.

## Files to Create
- `docs/launch-checklist.md`

## Checklist Categories

### Infrastructure
- [ ] `dev-api.kinnoo.ai` resolves and returns 200 on /health
- [ ] `dev.kinnoo.ai` loads the landing page
- [ ] S3 bucket exists and is accessible from ECS task
- [ ] EFS is mounted and auth store is accessible
- [ ] ALB health checks are passing
- [ ] Cloudflare proxy is active for dev-api.kinnoo.ai

### Security
- [ ] HTTPS is enforced (HTTP → HTTPS redirect)
- [ ] CORS only allows dev.kinnoo.ai origin
- [ ] Rate limiting is active
- [ ] Account lockout is working
- [ ] Token blacklist is working
- [ ] No open registration (invite-only)

### Documentation
- [ ] README.md is beta-ready
- [ ] docs/ folder has: kinnoo-yaml-spec, cli-reference, security-model, getting-started, registry-guide
- [ ] All docs are accurate and up-to-date

### CI/CD
- [ ] CI runs on every PR
- [ ] Backend deploys on main push
- [ ] Frontend deploys on main push
- [ ] Terraform plan/apply works

### Monitoring
- [ ] CloudWatch log group is receiving logs
- [ ] SNS alert subscriptions are confirmed
- [ ] Password reset SNS topic works
- [ ] 5xx alarm is configured

### User Onboarding
- [ ] Admin can create user via CLI
- [ ] User can login with temporary password
- [ ] User can change password
- [ ] User can publish an agent
- [ ] User can search and install agents
- [ ] Forgot password flow works end-to-end

### Registry Content
- [ ] At least 3 seed agents published
- [ ] Seed agents are searchable and installable
- [ ] At least one signed agent in registry

## Implementation Notes
- Each item should include: what to check, how to verify, expected result
- Include the actual commands to run for each verification step
- Printable format — Jerry can print and check off items

## Dependencies
- None (can be written at any time)

## Acceptance Criteria Summary
1. docs/launch-checklist.md exists with all categories
2. Each item has description, verification command, expected result
3. Covers: Infrastructure, Security, Docs, CI/CD, Monitoring, User Onboarding, Registry
4. Actionable — Jerry can follow step by step
