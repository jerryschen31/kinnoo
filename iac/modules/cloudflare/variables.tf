variable "zone_id" {
  description = "Cloudflare zone ID for kinnoo.ai"
  type        = string
}

variable "domain" {
  description = "Base domain name"
  type        = string
  default     = "kinnoo.ai"
}

variable "dev_record_type" {
  description = "DNS record type for dev.kinnoo.ai"
  type        = string
  default     = "CNAME"
}

variable "dev_record_content" {
  description = "DNS record content/target for dev.kinnoo.ai"
  type        = string
  default     = "kinnoo.pages.dev"
}

variable "manage_dev_record" {
  description = "Whether Terraform should manage the dev.kinnoo.ai DNS record"
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
