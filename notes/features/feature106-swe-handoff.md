# Feature 106 — SWE Handoff: Terraform Cloudflare DNS & Pages

## Context
Create Terraform module for Cloudflare DNS records and Pages project configuration.

## Files to Create
```
iac/modules/cloudflare/
├── main.tf          # DNS records, Pages project (if API allows)
├── variables.tf     # zone_id, domain, alb_dns_name, acm_validation_records
└── outputs.tf       # URLs
```

## DNS Records
1. `dev.kinnoo.ai` — CNAME to Cloudflare Pages deployment URL (e.g., `kinnoo.pages.dev`)
2. `dev-api.kinnoo.ai` — Proxied CNAME to ALB DNS name
3. ACM validation CNAME records (from feature105 ALB/ACM output)

## Implementation Notes
- Uses `cloudflare` Terraform provider
- Cloudflare API token from `CLOUDFLARE_API_TOKEN` env var
- Zone ID for `kinnoo.ai` from terraform.tfvars
- `dev-api.kinnoo.ai` should be **proxied** (orange cloud) so Cloudflare can filter traffic
- Cloudflare Pages project may need to be created manually if Terraform provider support is limited
- If Pages project is managed outside Terraform, just create the CNAME record

## terraform.tfvars additions
```hcl
cloudflare_zone_id    = "<zone-id>"  # Set by Jerry
cloudflare_account_id = "<account-id>"
domain                = "kinnoo.ai"
```

## Dependencies
- feature103 (project structure)
- feature105 (ALB DNS name output, ACM validation records)

## Acceptance Criteria Summary
1. DNS records for dev.kinnoo.ai and dev-api.kinnoo.ai
2. ACM validation CNAME records
3. Cloudflare API token from env var
4. `terraform validate` passes
