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
