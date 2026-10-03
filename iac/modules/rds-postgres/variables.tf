variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region for CLI/API calls made by guardrail scripts"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs used for DB subnet group"
  type        = list(string)
}

variable "db_security_group_id" {
  description = "Security group ID attached to Postgres instance"
  type        = string
}

variable "database_url_secret_arn" {
  description = "Optional secret ARN for REGISTRY_DATABASE_URL contract reference"
  type        = string
  default     = ""
}

variable "multi_az" {
  description = "Whether to run the DB instance in Multi-AZ mode."
  type        = bool
  default     = true
}

variable "allocated_storage" {
  description = "Allocated DB storage in GB"
  type        = number
  default     = 20
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "alarm_topic_arn" {
  description = "SNS topic ARN for database alarms"
  type        = string
  default     = ""
}

variable "master_secret_rotation_enabled" {
  description = "Whether rotation should be enabled for the RDS-managed master user secret"
  type        = bool
  default     = false
}

variable "master_secret_rotation_automatically_after_days" {
  description = "Rotation interval in days when master_secret_rotation_enabled is true"
  type        = number
  default     = 7
}

variable "sync_registry_database_url_on_rotation_apply" {
  description = "Whether to refresh REGISTRY_DATABASE_URL from the current RDS master secret during Terraform apply"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
