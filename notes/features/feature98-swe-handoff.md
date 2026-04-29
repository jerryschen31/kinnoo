# Feature 98 — SWE Handoff: GitHub Actions CI/CD Pipeline

## Context
Create comprehensive CI/CD workflows. Existing: `.github/workflows/ci.yml` and `kinnoo-publish.yml`.

## Files to Modify
- `.github/workflows/ci.yml` — Enhance existing CI workflow

## Files to Create
- `.github/workflows/deploy-backend.yml` — Build Docker → push ECR → update ECS
- `.github/workflows/deploy-frontend.yml` — Build Next.js → deploy Cloudflare Pages
- `.github/workflows/terraform.yml` — Plan on PR, apply on merge

## Workflow Details

### deploy-backend.yml
- Trigger: push to main
- Steps: checkout → configure AWS (OIDC) → login to ECR → build Docker image → push to ECR → update ECS service → wait for deployment → run smoke test
- Rollback: if smoke test fails, update ECS to previous task definition

### deploy-frontend.yml
- Trigger: push to main (web/ changes)
- Steps: checkout → install deps → build Next.js (`next build`) → deploy to Cloudflare Pages (wrangler)

### terraform.yml
- Trigger: PR (iac/ changes) → `terraform plan` as PR comment
- Trigger: push to main (iac/ changes) → `terraform apply -auto-approve`
- Uses OIDC for AWS credentials

## Implementation Notes
- OIDC provider must exist in AWS (created by IaC feature106)
- ECR repository created by feature105
- Use `aws-actions/configure-aws-credentials@v4` with OIDC
- Cloudflare Pages deployment via `cloudflare/wrangler-action@v3`
- Include deployment notifications (GitHub deployment status)

## Dependencies
- feature103, feature105 (IaC resources must exist)

## Acceptance Criteria Summary
1. CI runs tests on every PR
2. Backend deploys to ECS on main push
3. Frontend deploys to Cloudflare Pages on main push
4. Terraform plan on PR, apply on merge
5. OIDC for AWS credentials
