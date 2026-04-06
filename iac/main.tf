module "vpc" {
  source = "./modules/vpc"

  aws_region          = var.aws_region
  environment         = var.environment
  project_name        = var.project_name
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  tags                = local.common_tags
}
