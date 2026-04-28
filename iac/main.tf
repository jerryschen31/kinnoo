data "aws_caller_identity" "current" {}

locals {
  api_domain = "${var.api_record_name}.${var.base_domain}"
}

module "vpc" {
  source = "./modules/vpc"

  aws_region          = var.aws_region
  environment         = var.environment
  project_name        = var.project_name
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  tags                = local.common_tags
}

module "s3_registry" {
  source = "./modules/s3-registry"

  bucket_name = "${var.project_name}-registry-${var.environment}-${data.aws_caller_identity.current.account_id}"
  environment = var.environment
  tags        = local.common_tags
}

module "iam" {
  source = "./modules/iam"

  environment         = var.environment
  project_name        = var.project_name
  registry_bucket_arn = module.s3_registry.bucket_arn
  github_repo         = var.github_repo
  github_oidc_provider_url = var.github_oidc_provider_url
  manage_github_oidc_provider = var.manage_github_oidc_provider
  tags                = local.common_tags
}

module "lambda_security_check" {
  source = "./modules/lambda-security-check"

  project_name        = var.project_name
  environment         = var.environment
  lambda_role_arn     = module.iam.lambda_security_check_role_arn
  image_uri           = var.lambda_security_check_image_uri
  registry_bucket_arn = module.s3_registry.bucket_arn
  registry_bucket_id  = module.s3_registry.bucket_name
  tags                = local.common_tags
}

module "secrets" {
  source = "./modules/secrets"

  aws_region   = var.aws_region
  environment  = var.environment
  project_name = var.project_name
  tags         = local.common_tags
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "alb" {
  source = "./modules/alb"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  api_domain            = local.api_domain
  tags                  = local.common_tags
}

module "ecs_fargate" {
  source = "./modules/ecs-fargate"

  project_name               = var.project_name
  environment                = var.environment
  aws_region                 = var.aws_region
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.public_subnet_ids
  ecs_security_group_id      = module.vpc.ecs_security_group_id
  target_group_arn           = module.alb.target_group_arn
  execution_role_arn         = module.iam.ecs_execution_role_arn
  task_role_arn              = module.iam.ecs_task_role_arn
  image_url                  = "${module.ecr.repository_url}:latest"
  secret_arns                = module.secrets.secret_arns
  registry_bucket_name       = module.s3_registry.bucket_name
  sns_topic_arn              = var.sns_topic_arn
  security_check_lambda_name = module.lambda_security_check.function_name
  auth_provider              = var.auth_provider
  registry_metadata_backend  = var.registry_metadata_backend
  registry_db_pool_size      = var.registry_db_pool_size
  registry_db_max_overflow   = var.registry_db_max_overflow
  registry_db_pool_recycle_seconds = var.registry_db_pool_recycle_seconds
  tags                       = local.common_tags
}

module "rds_postgres" {
  source = "./modules/rds-postgres"

  project_name                    = var.project_name
  environment                     = var.environment
  private_subnet_ids              = module.vpc.private_subnet_ids
  db_security_group_id            = module.vpc.db_security_group_id
  database_url_secret_arn         = lookup(module.secrets.secret_arns, "REGISTRY_DATABASE_URL", "")
  alarm_topic_arn                 = var.sns_topic_arn
  tags                            = local.common_tags
}

module "cloudflare" {
  source = "./modules/cloudflare"

  zone_id               = var.zone_id
  domain                = var.base_domain
  api_record_name       = var.api_record_name
  frontend_record_name  = var.frontend_record_name
  frontend_record_type  = var.dev_record_type
  frontend_record_content = var.dev_record_content
  manage_frontend_record = var.manage_dev_record
  alb_dns_name          = module.alb.alb_dns_name
  acm_validation_record = module.alb.acm_validation_record
}
