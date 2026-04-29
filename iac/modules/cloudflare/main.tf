terraform {
  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
    }
  }
}

moved {
  from = cloudflare_record.dev_api
  to   = cloudflare_record.api
}

locals {
  frontend_host = var.frontend_subdomain
  api_host      = var.api_subdomain
}

resource "cloudflare_record" "frontend" {
  count   = var.manage_frontend_record ? 1 : 0
  zone_id = var.zone_id
  name    = local.frontend_host
  type    = var.frontend_record_type
  content = var.frontend_record_content
  ttl     = 1
  proxied = true
}

resource "cloudflare_record" "api" {
  zone_id = var.zone_id
  name    = local.api_host
  type    = "CNAME"
  content = var.alb_dns_name
  ttl     = 1
  proxied = true
}

resource "cloudflare_record" "acm_validation" {
  zone_id = var.zone_id
  name    = var.acm_validation_record.name
  type    = var.acm_validation_record.type
  content = var.acm_validation_record.value
  ttl     = var.acm_validation_record.ttl
  proxied = false
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "https://${local.frontend_host}.${var.domain}"
}

output "api_url" {
  description = "API URL"
  value       = "https://${local.api_host}.${var.domain}"
}

# Backwards-compatible aliases for downstream consumers that previously read
# dev_url / dev_api_url. Safe to remove after consumers migrate.
output "dev_url" {
  description = "Deprecated alias for frontend_url"
  value       = "https://${local.frontend_host}.${var.domain}"
}

output "dev_api_url" {
  description = "Deprecated alias for api_url"
  value       = "https://${local.api_host}.${var.domain}"
}
