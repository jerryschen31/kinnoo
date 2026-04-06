locals {
  # Shared tags keep module outputs consistent across phases.
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
