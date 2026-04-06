locals {
  dev_host     = "dev"
  dev_api_host = "dev-api"
}

resource "cloudflare_dns_record" "dev_pages" {
  zone_id = var.zone_id
  name    = local.dev_host
  type    = "CNAME"
  content = var.pages_target
  ttl     = 1
  proxied = true
}

resource "cloudflare_dns_record" "dev_api" {
  zone_id = var.zone_id
  name    = local.dev_api_host
  type    = "CNAME"
  content = var.alb_dns_name
  ttl     = 1
  proxied = true
}

resource "cloudflare_dns_record" "acm_validation" {
  for_each = {
    for record in var.acm_validation_records : record.name => record
  }

  zone_id = var.zone_id
  name    = each.value.name
  type    = each.value.type
  content = each.value.value
  ttl     = each.value.ttl
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
