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

output "dev_url" {
  description = "Dev frontend URL"
  value       = "https://${local.dev_host}.${var.domain}"
}

output "dev_api_url" {
  description = "Dev API URL"
  value       = "https://${local.dev_api_host}.${var.domain}"
}
