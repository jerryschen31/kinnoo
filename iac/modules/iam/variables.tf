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

variable "github_oidc_provider_url" {
  description = "OIDC provider URL for GitHub Actions"
  type        = string
  default     = "https://token.actions.githubusercontent.com"
}

variable "manage_github_oidc_provider" {
  description = "Whether this stack manages (creates) the GitHub OIDC provider"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
