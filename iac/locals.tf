locals {
  # Shared tags keep module outputs consistent across phases.
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # Resolve fully-qualified domain names from environment-specific subdomain
  # labels and the shared base domain. This keeps dev/prod DNS isolated and
  # lets a single root module serve both environments via tfvars.
  frontend_fqdn = "${var.frontend_subdomain}.${var.base_domain}"
  api_fqdn      = "${var.api_subdomain}.${var.base_domain}"

  # Backwards-compatibility shim: prefer new neutral inputs but fall back to
  # the deprecated dev_* inputs while existing tfvars are migrated.
  effective_frontend_record_type    = var.dev_record_type != "" ? var.dev_record_type : var.frontend_record_type
  effective_frontend_record_content = var.dev_record_content != "" ? var.dev_record_content : var.frontend_record_content
  effective_manage_frontend_record  = var.manage_frontend_record || var.manage_dev_record
}
