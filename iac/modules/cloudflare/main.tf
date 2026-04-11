terraform {
  required_providers {
    cloudflare = {
      source = "cloudflare/cloudflare"
    }
  }
}

locals {
  dev_host     = "dev"
  dev_api_host = "dev-api"
}

resource "cloudflare_record" "dev_pages" {
  count   = var.manage_dev_record ? 1 : 0
  zone_id = var.zone_id
  name    = local.dev_host
  type    = var.dev_record_type
  content = var.dev_record_content
  ttl     = 1
  proxied = true
}

resource "cloudflare_record" "dev_api" {
  zone_id = var.zone_id
  name    = local.dev_api_host
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

output "dev_url" {
  description = "Dev frontend URL"
  value       = "https://${local.dev_host}.${var.domain}"
}

output "dev_api_url" {
  description = "Dev API URL"
  value       = "https://${local.dev_api_host}.${var.domain}"
}
