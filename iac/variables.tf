variable "aws_region" {
  description = "AWS region for infrastructure"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used in resource naming"
  type        = string
  default     = "kinnoo"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for two public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token for later DNS modules"
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_repo" {
  description = "GitHub repository in owner/name format for OIDC trust"
  type        = string
  default     = "kinnoo/kinnoo"
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for operator notifications"
  type        = string
  default     = ""
}

variable "zone_id" {
  description = "Cloudflare zone ID for kinnoo.ai"
  type        = string
}
