terraform {
  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
    }
  }
}

locals {
  frontend_host = var.frontend_record_name
  api_host      = var.api_record_name
  frontend_fqdn = var.frontend_record_name == "@" ? var.domain : "${var.frontend_record_name}.${var.domain}"
}

moved {
  from = cloudflare_record.dev_api
  to   = cloudflare_record.api
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
  value       = "https://${local.frontend_fqdn}"
}

output "api_url" {
  description = "API URL"
  value       = "https://${local.api_host}.${var.domain}"
}
