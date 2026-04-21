output "address" {
  description = "Postgres endpoint address"
  value       = aws_db_instance.this.address
}

output "port" {
  description = "Postgres endpoint port"
  value       = aws_db_instance.this.port
}

output "db_instance_identifier" {
  description = "Postgres DB instance identifier"
  value       = aws_db_instance.this.id
}

output "database_name" {
  description = "Configured database name"
  value       = aws_db_instance.this.db_name
}

output "database_url_secret_arn" {
  description = "Contract secret arn for REGISTRY_DATABASE_URL"
  value       = var.database_url_secret_arn
}
