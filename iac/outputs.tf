output "vpc_id" {
  description = "VPC id for downstream modules"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet ids for ALB/ECS"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet ids for RDS"
  value       = module.vpc.private_subnet_ids
}

output "alb_security_group_id" {
  description = "ALB security group id"
  value       = module.vpc.alb_security_group_id
}

output "ecs_security_group_id" {
  description = "ECS security group id"
  value       = module.vpc.ecs_security_group_id
}

output "db_security_group_id" {
  description = "Postgres DB security group id"
  value       = module.vpc.db_security_group_id
}

output "ecr_repository_url" {
  description = "ECR repository URL for server image"
  value       = module.ecr.repository_url
}

output "lambda_security_check_ecr_repository_url" {
  description = "ECR repository URL for security-check Lambda image"
  value       = module.ecr.lambda_security_check_repository_url
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.alb_dns_name
}

output "alb_target_group_arn" {
  description = "ALB target group ARN"
  value       = module.alb.target_group_arn
}

output "acm_validation_record" {
  description = "ACM DNS validation record for Cloudflare"
  value       = module.alb.acm_validation_record
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

output "security_check_lambda_name" {
  description = "Security-check Lambda function name"
  value       = module.lambda_security_check.function_name
}

output "security_check_lambda_arn" {
  description = "Security-check Lambda function ARN"
  value       = module.lambda_security_check.function_arn
}

output "registry_db_endpoint" {
  description = "Postgres instance endpoint"
  value       = module.rds_postgres.address
}

output "registry_db_identifier" {
  description = "Postgres instance identifier"
  value       = module.rds_postgres.db_instance_identifier
}
