locals {
  secret_names = {
    JWT_SECRET     = "${var.project_name}/${var.environment}/jwt-secret"
    SESSION_SECRET = "${var.project_name}/${var.environment}/session-secret"
    ADMIN_PASSWORD = "${var.project_name}/${var.environment}/admin-password"
  }
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = local.secret_names.JWT_SECRET
  description             = "JWT signing key for ${var.project_name} ${var.environment}"
  recovery_window_in_days = 7
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "session_secret" {
  name                    = local.secret_names.SESSION_SECRET
  description             = "Session signing key for ${var.project_name} ${var.environment}"
  recovery_window_in_days = 7
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "admin_password" {
  name                    = local.secret_names.ADMIN_PASSWORD
  description             = "Bootstrap admin password for ${var.project_name} ${var.environment}"
  recovery_window_in_days = 7
  tags                    = var.tags
}

output "secret_arns" {
  description = "Secrets Manager ARNs for app runtime"
  value = {
    JWT_SECRET     = aws_secretsmanager_secret.jwt_secret.arn
    SESSION_SECRET = aws_secretsmanager_secret.session_secret.arn
    ADMIN_PASSWORD = aws_secretsmanager_secret.admin_password.arn
  }
}

output "secret_names" {
  description = "Secrets Manager names for runtime secret lookups"
  value       = local.secret_names
}
