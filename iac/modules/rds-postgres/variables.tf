variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
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

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
