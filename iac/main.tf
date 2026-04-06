data "aws_caller_identity" "current" {}

module "vpc" {
  source = "./modules/vpc"

  aws_region          = var.aws_region
  environment         = var.environment
  project_name        = var.project_name
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
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
  tags                = local.common_tags
}

module "secrets" {
  source = "./modules/secrets"

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

  project_name           = var.project_name
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  public_subnet_ids      = module.vpc.public_subnet_ids
  alb_security_group_id  = module.vpc.alb_security_group_id
  api_domain             = "dev-api.kinnoo.ai"
  tags                   = local.common_tags
}

module "ecs_fargate" {
  source = "./modules/ecs-fargate"

  project_name          = var.project_name
  environment           = var.environment
  aws_region            = var.aws_region
  vpc_id                = module.vpc.vpc_id
  subnet_ids            = module.vpc.public_subnet_ids
  ecs_security_group_id = module.vpc.ecs_security_group_id
  target_group_arn      = module.alb.target_group_arn
  execution_role_arn    = module.iam.ecs_execution_role_arn
  task_role_arn         = module.iam.ecs_task_role_arn
  image_url             = "${module.ecr.repository_url}:latest"
  secret_arns           = module.secrets.secret_arns
  registry_bucket_name  = module.s3_registry.bucket_name
  sns_topic_arn         = var.sns_topic_arn
  tags                  = local.common_tags
}

module "cloudflare" {
  source = "./modules/cloudflare"

  zone_id                 = var.zone_id
  domain                  = "kinnoo.ai"
  pages_target            = "kinnoo.pages.dev"
  alb_dns_name            = module.alb.alb_dns_name
  acm_validation_records  = module.alb.acm_validation_records
}
