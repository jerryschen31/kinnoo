aws_region          = "us-west-2"
environment         = "prod"
project_name        = "kinnoo"
vpc_cidr            = "10.10.0.0/16"
public_subnet_cidrs = ["10.10.1.0/24", "10.10.2.0/24"]
private_subnet_cidrs = ["10.10.101.0/24", "10.10.102.0/24"]

# --- Domain wiring (task518/task524) ---
# Production targets the apex/www frontend and api.kinnoo.ai for the API.
# Keep these labels strictly different from the dev tfvars so prod and dev
# Cloudflare records and ALB ACM certificates can never collide.
base_domain             = "kinnoo.ai"
frontend_subdomain      = "www"
api_subdomain           = "api"
# Cloudflare DNS for the frontend record. Default: do not let Terraform manage
# the apex/www record; manage it manually or via Cloudflare Pages until
# `manage_frontend_record` is explicitly flipped to true with a known target.
manage_frontend_record  = false
frontend_record_type    = "CNAME"
frontend_record_content = "kinnoo.pages.dev"

# --- Auth provider (task524) ---
# Required at runtime for ECS task env wiring; no default in iac/variables.tf.
auth_provider = "oidc_kinde"

# --- Registry metadata backend ---
registry_metadata_backend = "postgres"
registry_db_pool_size = 20
registry_db_max_overflow = 40
registry_db_pool_recycle_seconds = 1800

# --- Cloudflare zone (task524) ---
# Operator must paste the kinnoo.ai zone id here before first apply. Same
# zone as dev (one Cloudflare zone for kinnoo.ai), but DNS records inside the
# zone are kept separate by frontend_subdomain/api_subdomain above.
zone_id = "REPLACE_WITH_KINNOO_AI_ZONE_ID"

# --- Lambda security-check image (task523/task524) ---
# REQUIRED. iac/variables.tf declares this with `nullable = false` and a
# strict regex; Terraform plan will fail until this is set to a real prod
# ECR image URI.
#
# Bootstrap procedure (see notes/prod-deployment-instructions.md Phase 3):
#   1. terraform apply -target=module.ecr  (creates the prod ECR repo)
#   2. ENVIRONMENT=prod scripts/ops/build_and_push_lambda_security_check_image.sh
#   3. Replace the placeholder URI below with the real <account>.dkr.ecr.<region>.amazonaws.com/kinnoo-prod-lambda-security-check:<tag>
#   4. terraform apply (full stack)
#
# Example:
# lambda_security_check_image_uri = "123456789012.dkr.ecr.us-west-2.amazonaws.com/kinnoo-prod-lambda-security-check:v1"
#
# The placeholder below uses 12 zeros for the account id. It satisfies the
# regex in iac/variables.tf so `terraform validate` passes, but it is obviously
# not a real account id and any apply attempt against ECR will fail loudly
# until the operator replaces it.
lambda_security_check_image_uri = "000000000000.dkr.ecr.us-west-2.amazonaws.com/kinnoo-prod-lambda-security-check:bootstrap"
