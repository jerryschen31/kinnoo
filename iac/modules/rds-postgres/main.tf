locals {
  name_prefix = "${var.project_name}-${var.environment}"
  is_prod     = var.environment == "prod"
  # Keep dev/non-prod within stricter free-tier backup retention limits.
  backup_retention = 1
  database_name    = "kinnoo_registry"
}

resource "aws_db_subnet_group" "this" {
  name       = "${local.name_prefix}-postgres-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-postgres-subnet-group"
  })
}

resource "aws_db_instance" "this" {
  identifier                   = "${local.name_prefix}-postgres"
  engine                       = "postgres"
  engine_version               = "16.13"
  instance_class               = var.instance_class
  allocated_storage            = var.allocated_storage
  db_name                      = local.database_name
  username                     = "kinnoo_admin"
  manage_master_user_password  = true
  db_subnet_group_name         = aws_db_subnet_group.this.name
  vpc_security_group_ids       = [var.db_security_group_id]
  storage_encrypted            = true
  publicly_accessible          = false
  backup_retention_period      = local.backup_retention
  backup_window                = "03:00-04:00"
  maintenance_window           = "sun:05:00-sun:06:00"
  auto_minor_version_upgrade   = true
  apply_immediately            = !local.is_prod
  multi_az                     = local.is_prod
  deletion_protection          = local.is_prod
  performance_insights_enabled = true
  skip_final_snapshot          = false
  final_snapshot_identifier    = "${local.name_prefix}-postgres-final-snapshot"
  copy_tags_to_snapshot        = true

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-postgres"
  })
}

data "aws_secretsmanager_secret_rotation" "master_user" {
  secret_id = aws_db_instance.this.master_user_secret[0].secret_arn
}

# Guardrail: enforce desired rotation state for the RDS-managed master secret.
# This uses a local script because current aws_db_instance schema in this repo
# does not expose first-class rotation toggles.
resource "terraform_data" "master_secret_rotation_guardrail" {
  triggers_replace = {
    secret_arn     = aws_db_instance.this.master_user_secret[0].secret_arn
    desired_enabled = tostring(var.master_secret_rotation_enabled)
    desired_days    = tostring(var.master_secret_rotation_automatically_after_days)
    desired_sync    = tostring(var.sync_registry_database_url_on_rotation_apply)
    observed_enabled = tostring(data.aws_secretsmanager_secret_rotation.master_user.rotation_enabled)
    observed_days    = tostring(try(data.aws_secretsmanager_secret_rotation.master_user.rotation_rules[0].automatically_after_days, 0))
  }

  provisioner "local-exec" {
    command = <<-EOT
      "${path.module}/../../../scripts/ops/enforce-rds-master-secret-rotation.sh" \
        --secret-id "${aws_db_instance.this.master_user_secret[0].secret_arn}" \
        --enabled "${var.master_secret_rotation_enabled}" \
        --days "${var.master_secret_rotation_automatically_after_days}" \
        --region "${var.aws_region}" \
        --db-instance-identifier "${aws_db_instance.this.identifier}" \
        --environment "${var.environment}" \
        --project "${var.project_name}" \
        --sync-registry-database-url "${var.sync_registry_database_url_on_rotation_apply}"
    EOT
  }
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  count = var.alarm_topic_arn == "" ? 0 : 1

  alarm_name          = "${local.name_prefix}-postgres-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 75
  alarm_description   = "RDS CPU utilization high"
  alarm_actions       = [var.alarm_topic_arn]
  ok_actions          = [var.alarm_topic_arn]
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }
}

resource "aws_cloudwatch_metric_alarm" "free_storage_low" {
  count = var.alarm_topic_arn == "" ? 0 : 1

  alarm_name          = "${local.name_prefix}-postgres-free-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2147483648
  alarm_description   = "RDS free storage below 2GiB"
  alarm_actions       = [var.alarm_topic_arn]
  ok_actions          = [var.alarm_topic_arn]
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }
}

resource "aws_cloudwatch_metric_alarm" "connections_high" {
  count = var.alarm_topic_arn == "" ? 0 : 1

  alarm_name          = "${local.name_prefix}-postgres-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS connection count is approaching saturation"
  alarm_actions       = [var.alarm_topic_arn]
  ok_actions          = [var.alarm_topic_arn]
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }
}

resource "aws_cloudwatch_metric_alarm" "read_latency_high" {
  count = var.alarm_topic_arn == "" ? 0 : 1

  alarm_name          = "${local.name_prefix}-postgres-read-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ReadLatency"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = 0.2
  alarm_description   = "RDS read latency above 200ms"
  alarm_actions       = [var.alarm_topic_arn]
  ok_actions          = [var.alarm_topic_arn]
  dimensions = {
    DBInstanceIdentifier = aws_db_instance.this.id
  }
}
