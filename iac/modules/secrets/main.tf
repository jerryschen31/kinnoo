locals {
  managed_secret_names = {
    JWT_SECRET     = "${var.project_name}/${var.environment}/jwt-secret"
    SESSION_SECRET = "${var.project_name}/${var.environment}/session-secret"
    ADMIN_PASSWORD = "${var.project_name}/${var.environment}/admin-password"
  }

  # Auth secrets provisioned out-of-band and referenced (not managed) by Terraform.
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
    CORS_ORIGINS              = "${var.project_name}/${var.environment}/CORS_ORIGINS"
    REGISTRY_DATABASE_URL     = "/${var.project_name}/${var.environment}/REGISTRY_DATABASE_URL"
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

data "aws_secretsmanager_secret" "cors_origins" {
  name = local.referenced_secret_names.CORS_ORIGINS
}

data "aws_secretsmanager_secret" "registry_database_url" {
  name = local.referenced_secret_names.REGISTRY_DATABASE_URL
}

output "secret_arns" {
  description = "Secrets Manager ARNs for app runtime"
  value = {
    JWT_SECRET                           = aws_secretsmanager_secret.jwt_secret.arn
    SESSION_SECRET                       = aws_secretsmanager_secret.session_secret.arn
    ADMIN_PASSWORD                       = aws_secretsmanager_secret.admin_password.arn
    REGISTRY_TOKEN_SIGNING_SECRET        = aws_secretsmanager_secret.jwt_secret.arn
    REGISTRY_SESSION_SIGNING_SECRET      = aws_secretsmanager_secret.session_secret.arn
    REGISTRY_REGISTER_TOKEN_SECRET       = aws_secretsmanager_secret.jwt_secret.arn
    REGISTRY_PASSWORD_RESET_TOKEN_SECRET = aws_secretsmanager_secret.session_secret.arn
    AUTH_PROVIDER                        = format("%s:%s::", data.aws_secretsmanager_secret.auth_provider.arn, "AUTH_PROVIDER")
    AUTH_WEB_CLIENT_ID                   = format("%s:%s::", data.aws_secretsmanager_secret.kinde_web_client_id.arn, "KINDE_WEB_CLIENT_ID")
    AUTH_WEB_CLIENT_SECRET               = format("%s:%s::", data.aws_secretsmanager_secret.kinde_web_client_secret.arn, "KINDE_WEB_CLIENT_SECRET")
    AUTH_CLI_CLIENT_ID                   = format("%s:%s::", data.aws_secretsmanager_secret.kinde_cli_client_id.arn, "KINDE_CLI_CLIENT_ID")
    AUTH_ISSUER_URL                      = format("%s:%s::", data.aws_secretsmanager_secret.kinde_issuer_url.arn, "KINDE_ISSUER_URL")
    AUTH_AUDIENCE                        = format("%s:%s::", data.aws_secretsmanager_secret.kinde_audience.arn, "KINDE_AUDIENCE")
    AUTH_WEB_REDIRECT_URI                = format("%s:%s::", data.aws_secretsmanager_secret.kinde_web_redirect_uri.arn, "KINDE_WEB_REDIRECT_URI")
    AUTH_LOGOUT_REDIRECT_URI             = format("%s:%s::", data.aws_secretsmanager_secret.kinde_logout_redirect_uri.arn, "KINDE_LOGOUT_REDIRECT_URI")
    AUTH_JWKS_ENDPOINT_URL               = format("%s:%s::", data.aws_secretsmanager_secret.jwks_endpoint_url.arn, "JWKS_ENDPOINT_URL")
    AUTH_TOKEN_ENDPOINT                  = format("%s:%s::", data.aws_secretsmanager_secret.token_endpoint.arn, "TOKEN_ENDPOINT")
    AUTH_AUTHORIZATION_ENDPOINT          = format("%s:%s::", data.aws_secretsmanager_secret.authorization_endpoint.arn, "AUTHORIZATION_ENDPOINT")
    AUTH_LOGOUT_ENDPOINT                 = format("%s:%s::", data.aws_secretsmanager_secret.logout_endpoint.arn, "LOGOUT_ENDPOINT")
    AUTH_USERINFO_ENDPOINT               = format("%s:%s::", data.aws_secretsmanager_secret.userinfo_endpoint.arn, "USERINFO_ENDPOINT")
    AUTH_REVOCATION_ENDPOINT             = format("%s:%s::", data.aws_secretsmanager_secret.revocation_endpoint.arn, "REVOCATION_ENDPOINT")
    KINDE_WEB_CLIENT_ID                  = format("%s:%s::", data.aws_secretsmanager_secret.kinde_web_client_id.arn, "KINDE_WEB_CLIENT_ID")
    KINDE_WEB_CLIENT_SECRET              = format("%s:%s::", data.aws_secretsmanager_secret.kinde_web_client_secret.arn, "KINDE_WEB_CLIENT_SECRET")
    KINDE_CLI_CLIENT_ID                  = format("%s:%s::", data.aws_secretsmanager_secret.kinde_cli_client_id.arn, "KINDE_CLI_CLIENT_ID")
    KINDE_ISSUER_URL                     = format("%s:%s::", data.aws_secretsmanager_secret.kinde_issuer_url.arn, "KINDE_ISSUER_URL")
    KINDE_AUDIENCE                       = format("%s:%s::", data.aws_secretsmanager_secret.kinde_audience.arn, "KINDE_AUDIENCE")
    KINDE_WEB_REDIRECT_URI               = format("%s:%s::", data.aws_secretsmanager_secret.kinde_web_redirect_uri.arn, "KINDE_WEB_REDIRECT_URI")
    KINDE_LOGOUT_REDIRECT_URI            = format("%s:%s::", data.aws_secretsmanager_secret.kinde_logout_redirect_uri.arn, "KINDE_LOGOUT_REDIRECT_URI")
    JWKS_ENDPOINT_URL                    = format("%s:%s::", data.aws_secretsmanager_secret.jwks_endpoint_url.arn, "JWKS_ENDPOINT_URL")
    TOKEN_ENDPOINT                       = format("%s:%s::", data.aws_secretsmanager_secret.token_endpoint.arn, "TOKEN_ENDPOINT")
    AUTHORIZATION_ENDPOINT               = format("%s:%s::", data.aws_secretsmanager_secret.authorization_endpoint.arn, "AUTHORIZATION_ENDPOINT")
    LOGOUT_ENDPOINT                      = format("%s:%s::", data.aws_secretsmanager_secret.logout_endpoint.arn, "LOGOUT_ENDPOINT")
    USERINFO_ENDPOINT                    = format("%s:%s::", data.aws_secretsmanager_secret.userinfo_endpoint.arn, "USERINFO_ENDPOINT")
    REVOCATION_ENDPOINT                  = format("%s:%s::", data.aws_secretsmanager_secret.revocation_endpoint.arn, "REVOCATION_ENDPOINT")
    CORS_ORIGINS                         = data.aws_secretsmanager_secret.cors_origins.arn
    REGISTRY_DATABASE_URL                = format("%s:%s::", data.aws_secretsmanager_secret.registry_database_url.arn, "REGISTRY_DATABASE_URL")
  }
}

output "secret_names" {
  description = "Secrets Manager names for runtime secret lookups"
  value       = local.secret_names
}
