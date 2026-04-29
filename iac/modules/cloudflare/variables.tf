variable "zone_id" {
  description = "Cloudflare zone ID for kinnoo.ai"
  type        = string
}

variable "domain" {
  description = "Base domain name (e.g. kinnoo.ai)"
  type        = string
  default     = "kinnoo.ai"
}

variable "frontend_subdomain" {
  description = "Frontend subdomain label (e.g. dev for dev.kinnoo.ai)."
  type        = string
}

variable "api_subdomain" {
  description = "API subdomain label (e.g. dev-api for dev-api.kinnoo.ai)."
  type        = string
}

variable "frontend_record_type" {
  description = "DNS record type for the frontend record."
  type        = string
  default     = "CNAME"
}

variable "frontend_record_content" {
  description = "DNS record content/target for the frontend record."
  type        = string
  default     = "kinnoo.pages.dev"
}

variable "manage_frontend_record" {
  description = "Whether Terraform should manage the frontend DNS record."
  type        = bool
  default     = false
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
