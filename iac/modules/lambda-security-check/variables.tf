variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "lambda_role_arn" {
  description = "IAM role ARN for the security check Lambda"
  type        = string
}

variable "image_uri" {
  description = "Container image URI for the security check Lambda"
  type        = string
  default     = "386775099533.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-lambda-security-check:latest"
}

variable "registry_bucket_arn" {
  description = "ARN of the registry S3 bucket that emits publish events"
  type        = string
}

variable "registry_bucket_id" {
  description = "Name/id of the registry S3 bucket that emits publish events"
  type        = string
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
