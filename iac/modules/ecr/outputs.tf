output "repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.server.name
}

output "repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.server.repository_url
}

output "repository_arn" {
  description = "ECR repository ARN"
  value       = aws_ecr_repository.server.arn
}

output "lambda_security_check_repository_name" {
  description = "ECR repository name for security-check Lambda image"
  value       = aws_ecr_repository.lambda_security_check.name
}

output "lambda_security_check_repository_url" {
  description = "ECR repository URL for security-check Lambda image"
  value       = aws_ecr_repository.lambda_security_check.repository_url
}

output "lambda_security_check_repository_arn" {
  description = "ECR repository ARN for security-check Lambda image"
  value       = aws_ecr_repository.lambda_security_check.arn
}