aws_region          = "us-west-2"
environment         = "prod"
project_name        = "kinnoo"
manage_github_oidc_provider = false
vpc_cidr            = "10.10.0.0/16"
public_subnet_cidrs = ["10.10.1.0/24", "10.10.2.0/24"]
private_subnet_cidrs = ["10.10.101.0/24", "10.10.102.0/24"]
base_domain         = "kinnoo.ai"
api_record_name     = "api"
frontend_record_name = "@"
dev_record_type     = "CNAME"
dev_record_content  = "kinnoo.pages.dev"
manage_dev_record   = false
registry_metadata_backend = "postgres"
registry_db_pool_size = 10
registry_db_max_overflow = 20
registry_db_pool_recycle_seconds = 1800

lambda_security_check_image_uri = "386775099533.dkr.ecr.us-west-2.amazonaws.com/kinnoo-prod-lambda-security-check:latest"
auth_provider = "oidc_kinde"

