aws_region                  = "us-west-2"
environment                 = "dev"
project_name                = "kinnoo"
manage_github_oidc_provider = false
enable_dev_runtime          = true
enable_dev_database         = true
vpc_cidr                    = "10.0.0.0/16"
public_subnet_cidrs         = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs        = ["10.0.101.0/24", "10.0.102.0/24"]

# Domain wiring (task518): per-environment subdomain labels keep dev/prod
# Cloudflare records and ALB ACM certificates strictly isolated.
base_domain             = "kinnoo.ai"
frontend_subdomain      = "dev"
api_subdomain           = "dev-api"
frontend_record_type    = "AAAA"
frontend_record_content = "100::"
manage_frontend_record  = false

auth_provider                    = "oidc_kinde"
cors_origins                     = "https://dev.kinnoo.ai"
registry_metadata_backend        = "postgres" # "json"
registry_db_pool_size            = 10
registry_db_max_overflow         = 20
registry_db_pool_recycle_seconds = 1800
rds_master_secret_rotation_enabled                  = false
rds_master_secret_rotation_automatically_after_days = 7
rds_sync_registry_database_url_on_rotation_apply    = true

# Set this to the pushed Lambda image URI from your account ECR.
# Example: 123456789012.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-lambda-security-check:v1
lambda_security_check_image_uri = "386775099533.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-lambda-security-check:latest"

zone_id = "374008a2e2e60744960d315cd526a384"

# Database vars
# registry_metadata_backend = "postgres" # or "json" for fallback DB
# registry_db_pool_size = 10
# registry_db_max_overflow = 20
# registry_db_pool_recycle_seconds = 1800
