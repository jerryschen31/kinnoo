variable "zone_id" {
  description = "Cloudflare zone ID for kinnoo.ai"
  type        = string
}

variable "domain" {
  description = "Base domain name"
  type        = string
  default     = "kinnoo.ai"
}

variable "pages_target" {
  description = "Cloudflare Pages hostname target"
  type        = string
  default     = "kinnoo.pages.dev"
}

variable "alb_dns_name" {
  description = "ALB DNS name for API CNAME"
  type        = string
}

variable "acm_validation_record" {
  description = "ACM validation CNAME record to publish in Cloudflare"
  type = object({
    name  = string
    type  = string
    value = string
    ttl   = number
  })
}
