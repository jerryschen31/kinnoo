variable "zone_id" {
  description = "Cloudflare zone ID for kinnoo.ai"
  type        = string
}

variable "domain" {
  description = "Base domain name"
  type        = string
  default     = "kinnoo.ai"
}

variable "api_record_name" {
  description = "DNS host label for API endpoint record"
  type        = string
  default     = "dev-api"
}

variable "frontend_record_name" {
  description = "DNS host label for frontend endpoint record"
  type        = string
  default     = "dev"
}

variable "frontend_record_type" {
  description = "DNS record type for frontend endpoint record"
  type        = string
  default     = "CNAME"
}

variable "frontend_record_content" {
  description = "DNS record content/target for frontend endpoint record"
  type        = string
  default     = "kinnoo.pages.dev"
}

variable "manage_frontend_record" {
  description = "Whether Terraform should manage the frontend endpoint record"
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
