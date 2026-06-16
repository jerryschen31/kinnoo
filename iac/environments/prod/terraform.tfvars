aws_region                  = "us-west-2"
environment                 = "prod"
project_name                = "kinnoo"
manage_github_oidc_provider = true
enable_dev_runtime          = true
enable_dev_database         = true
vpc_cidr                    = "10.10.0.0/16"
public_subnet_cidrs         = ["10.10.1.0/24", "10.10.2.0/24"]
private_subnet_cidrs        = ["10.10.101.0/24", "10.10.102.0/24"]

# --- Domain wiring (task518/task524) ---
# Production targets the apex/www frontend and api.kinnoo.ai for the API.
# Keep these labels strictly different from the dev tfvars so prod and dev
# Cloudflare records and ALB ACM certificates can never collide.
base_domain        = "kinnoo.ai"
frontend_subdomain = "www"
api_subdomain      = "api"
# Cloudflare DNS for the frontend record. Default: do not let Terraform manage
# the apex/www record; manage it manually or via Cloudflare Pages until
# `manage_frontend_record` is explicitly flipped to true with a known target.
manage_frontend_record  = false
frontend_record_type    = "CNAME"
frontend_record_content = "kinnoo.pages.dev"

# --- Auth provider (task524) ---
# Required at runtime for ECS task env wiring; no default in iac/variables.tf.
auth_provider = "oidc_kinde"
cors_origins  = "https://kinnoo.ai,https://www.kinnoo.ai"

# --- Registry metadata backend ---
registry_metadata_backend                           = "postgres"
registry_db_pool_size                               = 20
registry_db_max_overflow                            = 40
registry_db_pool_recycle_seconds                    = 1800
rds_multi_az                                        = false
rds_master_secret_rotation_enabled                  = false
rds_master_secret_rotation_automatically_after_days = 7
rds_sync_registry_database_url_on_rotation_apply    = true
alb_enable_waf                                      = false

# --- Cloudflare zone (task524) ---
# Same kinnoo.ai zone as dev; DNS records are isolated by frontend_subdomain/
# api_subdomain above.
zone_id = "374008a2e2e60744960d315cd526a384"

# --- Lambda security-check image (task523/task524) ---
lambda_security_check_image_uri = "386775099533.dkr.ecr.us-west-2.amazonaws.com/kinnoo-prod-lambda-security-check:latest"
