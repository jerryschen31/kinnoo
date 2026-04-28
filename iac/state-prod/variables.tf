variable "aws_region" {
  description = "AWS region for bootstrap resources"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment label"
  type        = string
  default     = "prod"
}

variable "state_bucket_name" {
  description = "S3 bucket name for Terraform state backend"
  type        = string
  default     = "kinnoo-terraform-state-prod"
}
