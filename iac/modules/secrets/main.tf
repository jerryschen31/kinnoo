locals {
  managed_secret_names = {
    JWT_SECRET     = "${var.project_name}/${var.environment}/jwt-secret"
    SESSION_SECRET = "${var.project_name}/${var.environment}/session-secret"
    ADMIN_PASSWORD = "${var.project_name}/${var.environment}/admin-password"
  }

  # These auth secrets are provisioned out-of-band and referenced by Terraform.
  referenced_secret_names = {
    AUTH_PROVIDER             = "${var.project_name}/${var.environment}/AUTH_PROVIDER"
    KINDE_WEB_CLIENT_ID       = "${var.project_name}/${var.environment}/KINDE_WEB_CLIENT_ID"
    KINDE_WEB_CLIENT_SECRET   = "${var.project_name}/${var.environment}/KINDE_WEB_CLIENT_SECRET"
    KINDE_CLI_CLIENT_ID       = "${var.project_name}/${var.environment}/KINDE_CLI_CLIENT_ID"
    KINDE_ISSUER_URL          = "${var.project_name}/${var.environment}/KINDE_ISSUER_URL"
    KINDE_AUDIENCE            = "${var.project_name}/${var.environment}/KINDE_AUDIENCE"
    KINDE_WEB_REDIRECT_URI    = "${var.project_name}/${var.environment}/KINDE_WEB_REDIRECT_URI"
    KINDE_LOGOUT_REDIRECT_URI = "${var.project_name}/${var.environment}/KINDE_LOGOUT_REDIRECT_URI"
    JWKS_ENDPOINT_URL         = "${var.project_name}/${var.environment}/JWKS_ENDPOINT_URL"
    TOKEN_ENDPOINT            = "${var.project_name}/${var.environment}/TOKEN_ENDPOINT"
    AUTHORIZATION_ENDPOINT    = "${var.project_name}/${var.environment}/AUTHORIZATION_ENDPOINT"
    LOGOUT_ENDPOINT           = "${var.project_name}/${var.environment}/LOGOUT_ENDPOINT"
    USERINFO_ENDPOINT         = "${var.project_name}/${var.environment}/USERINFO_ENDPOINT"
    REVOCATION_ENDPOINT       = "${var.project_name}/${var.environment}/REVOCATION_ENDPOINT"
  }

  secret_names = merge(local.managed_secret_names, local.referenced_secret_names)
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = local.managed_secret_names.JWT_SECRET
  description             = "JWT signing key for ${var.project_name} ${var.environment}"
  recovery_window_in_days = 7
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "session_secret" {
  name                    = local.managed_secret_names.SESSION_SECRET
  description             = "Session signing key for ${var.project_name} ${var.environment}"
  recovery_window_in_days = 7
  tags                    = var.tags
}

resource "aws_secretsmanager_secret" "admin_password" {
  name                    = local.managed_secret_names.ADMIN_PASSWORD
  description             = "Bootstrap admin password for ${var.project_name} ${var.environment}"
  recovery_window_in_days = 7
  tags                    = var.tags
}

data "aws_secretsmanager_secret" "auth_provider" {
  name = local.referenced_secret_names.AUTH_PROVIDER
}

data "aws_secretsmanager_secret" "kinde_web_client_id" {
  name = local.referenced_secret_names.KINDE_WEB_CLIENT_ID
}

data "aws_secretsmanager_secret" "kinde_web_client_secret" {
  name = local.referenced_secret_names.KINDE_WEB_CLIENT_SECRET
}

data "aws_secretsmanager_secret" "kinde_cli_client_id" {
  name = local.referenced_secret_names.KINDE_CLI_CLIENT_ID
}

data "aws_secretsmanager_secret" "kinde_issuer_url" {
  name = local.referenced_secret_names.KINDE_ISSUER_URL
}

data "aws_secretsmanager_secret" "kinde_audience" {
  name = local.referenced_secret_names.KINDE_AUDIENCE
}

data "aws_secretsmanager_secret" "kinde_web_redirect_uri" {
  name = local.referenced_secret_names.KINDE_WEB_REDIRECT_URI
}

data "aws_secretsmanager_secret" "kinde_logout_redirect_uri" {
  name = local.referenced_secret_names.KINDE_LOGOUT_REDIRECT_URI
}

data "aws_secretsmanager_secret" "jwks_endpoint_url" {
  name = local.referenced_secret_names.JWKS_ENDPOINT_URL
}

data "aws_secretsmanager_secret" "token_endpoint" {
  name = local.referenced_secret_names.TOKEN_ENDPOINT
}

data "aws_secretsmanager_secret" "authorization_endpoint" {
  name = local.referenced_secret_names.AUTHORIZATION_ENDPOINT
}

data "aws_secretsmanager_secret" "logout_endpoint" {
  name = local.referenced_secret_names.LOGOUT_ENDPOINT
}

data "aws_secretsmanager_secret" "userinfo_endpoint" {
  name = local.referenced_secret_names.USERINFO_ENDPOINT
}

data "aws_secretsmanager_secret" "revocation_endpoint" {
  name = local.referenced_secret_names.REVOCATION_ENDPOINT
}

output "secret_arns" {
  description = "Secrets Manager ARNs for app runtime"
  value = {
    JWT_SECRET                = aws_secretsmanager_secret.jwt_secret.arn
    SESSION_SECRET            = aws_secretsmanager_secret.session_secret.arn
    ADMIN_PASSWORD            = aws_secretsmanager_secret.admin_password.arn
    AUTH_PROVIDER             = data.aws_secretsmanager_secret.auth_provider.arn
    AUTH_WEB_CLIENT_ID        = data.aws_secretsmanager_secret.kinde_web_client_id.arn
    AUTH_WEB_CLIENT_SECRET    = data.aws_secretsmanager_secret.kinde_web_client_secret.arn
    AUTH_CLI_CLIENT_ID        = data.aws_secretsmanager_secret.kinde_cli_client_id.arn
    AUTH_ISSUER_URL           = data.aws_secretsmanager_secret.kinde_issuer_url.arn
    AUTH_AUDIENCE             = data.aws_secretsmanager_secret.kinde_audience.arn
    AUTH_WEB_REDIRECT_URI     = data.aws_secretsmanager_secret.kinde_web_redirect_uri.arn
    AUTH_LOGOUT_REDIRECT_URI  = data.aws_secretsmanager_secret.kinde_logout_redirect_uri.arn
    AUTH_JWKS_ENDPOINT_URL    = data.aws_secretsmanager_secret.jwks_endpoint_url.arn
    AUTH_TOKEN_ENDPOINT       = data.aws_secretsmanager_secret.token_endpoint.arn
    AUTH_AUTHORIZATION_ENDPOINT = data.aws_secretsmanager_secret.authorization_endpoint.arn
    AUTH_LOGOUT_ENDPOINT      = data.aws_secretsmanager_secret.logout_endpoint.arn
    AUTH_USERINFO_ENDPOINT    = data.aws_secretsmanager_secret.userinfo_endpoint.arn
    AUTH_REVOCATION_ENDPOINT  = data.aws_secretsmanager_secret.revocation_endpoint.arn
    KINDE_WEB_CLIENT_ID       = data.aws_secretsmanager_secret.kinde_web_client_id.arn
    KINDE_WEB_CLIENT_SECRET   = data.aws_secretsmanager_secret.kinde_web_client_secret.arn
    KINDE_CLI_CLIENT_ID       = data.aws_secretsmanager_secret.kinde_cli_client_id.arn
    KINDE_ISSUER_URL          = data.aws_secretsmanager_secret.kinde_issuer_url.arn
    KINDE_AUDIENCE            = data.aws_secretsmanager_secret.kinde_audience.arn
    KINDE_WEB_REDIRECT_URI    = data.aws_secretsmanager_secret.kinde_web_redirect_uri.arn
    KINDE_LOGOUT_REDIRECT_URI = data.aws_secretsmanager_secret.kinde_logout_redirect_uri.arn
    JWKS_ENDPOINT_URL         = data.aws_secretsmanager_secret.jwks_endpoint_url.arn
    TOKEN_ENDPOINT            = data.aws_secretsmanager_secret.token_endpoint.arn
    AUTHORIZATION_ENDPOINT    = data.aws_secretsmanager_secret.authorization_endpoint.arn
    LOGOUT_ENDPOINT           = data.aws_secretsmanager_secret.logout_endpoint.arn
    USERINFO_ENDPOINT         = data.aws_secretsmanager_secret.userinfo_endpoint.arn
    REVOCATION_ENDPOINT       = data.aws_secretsmanager_secret.revocation_endpoint.arn
  }
}

output "secret_names" {
  description = "Secrets Manager names for runtime secret lookups"
  value       = local.secret_names
}
