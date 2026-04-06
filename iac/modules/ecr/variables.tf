variable "project_name" {
  description = "Project name for ECR naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}