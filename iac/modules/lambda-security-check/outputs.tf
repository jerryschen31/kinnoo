output "function_name" {
  description = "Lambda function name for security checks"
  value       = aws_lambda_function.security_check.function_name
}

output "function_arn" {
  description = "Lambda function ARN for security checks"
  value       = aws_lambda_function.security_check.arn
}
