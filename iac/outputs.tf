output "vpc_id" {
  description = "VPC id for downstream modules"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet ids for ALB/ECS"
  value       = module.vpc.public_subnet_ids
}

output "alb_security_group_id" {
  description = "ALB security group id"
  value       = module.vpc.alb_security_group_id
}

output "ecs_security_group_id" {
  description = "ECS security group id"
  value       = module.vpc.ecs_security_group_id
}
