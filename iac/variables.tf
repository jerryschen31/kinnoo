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

variable "private_subnet_cidrs" {
  description = "CIDR blocks for two private subnets used by RDS"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
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

variable "manage_github_oidc_provider" {
  description = "Whether this environment manages the shared GitHub OIDC provider in AWS IAM"
  type        = bool
  default     = false
}

variable "enable_dev_runtime" {
  description = "Dev-only toggle for runtime stack modules (ALB, ECS, WAF, Cloudflare API/ACM records). Ignored outside dev."
  type        = bool
  default     = true
}

variable "enable_dev_database" {
  description = "Dev-only toggle for the Postgres database module. Ignored outside dev."
  type        = bool
  default     = true
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for operator notifications"
  type        = string
  default     = ""
}

variable "auth_provider" {
  description = "Runtime auth provider identifier for ECS environment configuration"
  type        = string
  default     = "oidc_kinde"
}

variable "cors_origins" {
  description = "Comma-separated CORS origins passed to ECS runtime"
  type        = string
  default     = ""
}

variable "registry_metadata_backend" {
  description = "Metadata backend mode for registry runtime"
  type        = string
  default     = "json"
}

variable "registry_db_pool_size" {
  description = "Database connection pool size for registry runtime"
  type        = number
  default     = 10
}

variable "registry_db_max_overflow" {
  description = "Database max overflow connections for registry runtime"
  type        = number
  default     = 20
}

variable "registry_db_pool_recycle_seconds" {
  description = "Database pool recycle window in seconds"
  type        = number
  default     = 1800
}

variable "rds_master_secret_rotation_enabled" {
  description = "Whether rotation is enabled for the RDS-managed master user secret"
  type        = bool
  default     = false
}

variable "rds_master_secret_rotation_automatically_after_days" {
  description = "Rotation interval in days when rds_master_secret_rotation_enabled is true"
  type        = number
  default     = 7

  validation {
    condition     = var.rds_master_secret_rotation_automatically_after_days >= 1
    error_message = "rds_master_secret_rotation_automatically_after_days must be >= 1."
  }
}

variable "rds_sync_registry_database_url_on_rotation_apply" {
  description = "Whether Terraform apply should refresh REGISTRY_DATABASE_URL from the current RDS master secret"
  type        = bool
  default     = true
}

variable "zone_id" {
  description = "Cloudflare zone ID for kinnoo.ai"
  type        = string
}

variable "base_domain" {
  description = "Base apex domain for kinnoo (e.g. kinnoo.ai). Shared by all environments."
  type        = string
  default     = "kinnoo.ai"
}

variable "frontend_subdomain" {
  description = "Subdomain label for the frontend (e.g. dev for dev.kinnoo.ai, www or empty for prod)."
  type        = string
  default     = "dev"
}

variable "api_subdomain" {
  description = "Subdomain label for the API ALB (e.g. dev-api for dev-api.kinnoo.ai, api for api.kinnoo.ai)."
  type        = string
  default     = "dev-api"
}

variable "frontend_record_type" {
  description = "DNS record type for the frontend record (CNAME, AAAA, etc.)."
  type        = string
  default     = "CNAME"
}

variable "frontend_record_content" {
  description = "DNS record content/target for the frontend record (e.g. kinnoo.pages.dev)."
  type        = string
  default     = "kinnoo.pages.dev"
}

variable "manage_frontend_record" {
  description = "Whether Terraform should manage the frontend DNS record in Cloudflare."
  type        = bool
  default     = false
}

# Backwards-compatible aliases for the old dev_*-prefixed inputs. These remain
# so existing tfvars do not break, but new tfvars should set the neutral
# frontend_* / api_subdomain inputs above.
variable "dev_record_type" {
  description = "Deprecated: use frontend_record_type."
  type        = string
  default     = ""
}

variable "dev_record_content" {
  description = "Deprecated: use frontend_record_content."
  type        = string
  default     = ""
}

variable "manage_dev_record" {
  description = "Deprecated: use manage_frontend_record."
  type        = bool
  default     = false
}

variable "lambda_security_check_image_uri" {
  description = "Container image URI for the security-check Lambda function"
  type        = string
  nullable    = false

  validation {
    condition = (
      length(trimspace(var.lambda_security_check_image_uri)) > 0
      && can(regex("^[0-9]{12}\\.dkr\\.ecr\\.[a-z0-9-]+\\.amazonaws\\.com\\/.+:.+$", var.lambda_security_check_image_uri))
    )
    error_message = "Set lambda_security_check_image_uri to a full private ECR image URI with tag (example: 123456789012.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-lambda-security-check:v1). Do not use a public Lambda base image URI."
  }

  validation {
    # Reject the well-known bootstrap placeholder (12 zeros for the account
    # id) so a forgotten tfvars edit cannot silently apply against AWS. The
    # placeholder is intentionally regex-valid so `terraform validate` passes
    # for static scanning, but `terraform plan/apply` must refuse it.
    condition     = !can(regex("^0{12}\\.dkr\\.ecr\\.", var.lambda_security_check_image_uri))
    error_message = "lambda_security_check_image_uri is still set to the 000000000000 bootstrap placeholder. Run scripts/ops/build_and_push_lambda_security_check_image.sh and replace the value with the real ECR image URI."
  }
}
