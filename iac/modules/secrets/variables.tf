variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_name" {
  description = "Project name used in secret naming"
  type        = string
}

variable "aws_region" {
  description = "AWS region for secret lookups"
  type        = string
  default     = "us-west-2"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
