variable "project_name" {
  description = "Project name for naming resources"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region for ECS and logs"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for EFS security group"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for ECS service and EFS mount targets"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID used by ECS tasks"
  type        = string
}

variable "target_group_arn" {
  description = "ALB target group ARN for ECS service"
  type        = string
}

variable "execution_role_arn" {
  description = "IAM execution role ARN for ECS task definition"
  type        = string
}

variable "task_role_arn" {
  description = "IAM task role ARN for ECS task definition"
  type        = string
}

variable "image_url" {
  description = "Container image URL to deploy"
  type        = string
}

variable "secret_arns" {
  description = "Map of secret environment variable names to Secrets Manager ARNs"
  type        = map(string)
  default     = {}
}

variable "registry_bucket_name" {
  description = "S3 registry bucket name for app configuration"
  type        = string
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for forgot-password/operator alerts"
  type        = string
  default     = ""
}

variable "security_check_lambda_name" {
  description = "Lambda function name used for async security checks"
  type        = string
  default     = ""
}

variable "auth_provider" {
  description = "Provider identifier exposed to runtime auth configuration"
  type        = string
  default     = "oidc_kinde"
}

variable "registry_metadata_backend" {
  description = "Metadata backend mode exposed to runtime"
  type        = string
  default     = "json"
}

variable "registry_db_pool_size" {
  description = "Database pool size for runtime"
  type        = number
  default     = 10
}

variable "registry_db_max_overflow" {
  description = "Database max overflow for runtime"
  type        = number
  default     = 20
}

variable "registry_db_pool_recycle_seconds" {
  description = "Database pool recycle setting for runtime"
  type        = number
  default     = 1800
}

variable "cpu" {
  description = "Fargate task CPU units"
  type        = number
  default     = 512
}

variable "memory" {
  description = "Fargate task memory (MiB)"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired ECS service task count"
  type        = number
  default     = 1
}

variable "container_port" {
  description = "Container listening port"
  type        = number
  default     = 8000
}

variable "enable_execute_command" {
  description = "Whether ECS Exec is enabled for the service"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
