module "vpc" {
  source = "./modules/vpc"

  aws_region          = var.aws_region
  environment         = var.environment
  project_name        = var.project_name
  vpc_cidr            = var.vpc_cidr
  public_subnet_cidrs = var.public_subnet_cidrs
  tags                = local.common_tags
}

module "cloudflare" {
  source = "./modules/cloudflare"

  zone_id      = var.zone_id
  domain       = "kinnoo.ai"
  pages_target = "kinnoo.pages.dev"
  alb_dns_name = var.alb_dns_name
}
