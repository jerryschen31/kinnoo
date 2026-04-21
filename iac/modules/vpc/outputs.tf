output "vpc_id" {
  description = "VPC id"
  value       = aws_vpc.this.id
}

output "public_subnet_ids" {
  description = "Public subnet ids"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet ids"
  value       = aws_subnet.private[*].id
}

output "alb_security_group_id" {
  description = "ALB security group id"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ECS security group id"
  value       = aws_security_group.ecs.id
}

output "db_security_group_id" {
  description = "Database security group id"
  value       = aws_security_group.db.id
}

output "vpc_endpoint_security_group_id" {
  description = "VPC endpoint security group id"
  value       = aws_security_group.vpc_endpoint.id
}
