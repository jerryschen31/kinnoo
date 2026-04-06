variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_name" {
  description = "Project name for naming IAM resources"
  type        = string
}

variable "registry_bucket_arn" {
  description = "ARN of S3 registry bucket"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository in owner/name format"
  type        = string
  default     = "kinnoo/kinnoo"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
