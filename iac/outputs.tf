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

output "ecr_repository_url" {
  description = "ECR repository URL for server image"
  value       = module.ecr.repository_url
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.alb_dns_name
}

output "alb_target_group_arn" {
  description = "ALB target group ARN"
  value       = module.alb.target_group_arn
}

output "acm_validation_records" {
  description = "ACM DNS validation records for Cloudflare"
  value       = module.alb.acm_validation_records
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = module.ecs_fargate.cluster_arn
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs_fargate.service_name
}

output "efs_file_system_id" {
  description = "EFS file system ID"
  value       = module.ecs_fargate.efs_file_system_id
}
