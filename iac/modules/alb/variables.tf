variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for target group"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for ALB"
  type        = string
}

variable "api_domain" {
  description = "API domain to bind ACM certificate"
  type        = string
  default     = "dev-api.kinnoo.ai"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}