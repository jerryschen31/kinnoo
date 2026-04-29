# Feature 107 — SWE Handoff: Terraform Monitoring

## Context
Create Terraform module for CloudWatch log groups, alarms, and SNS topics.

## Files to Create
```
iac/modules/monitoring/
├── main.tf          # CloudWatch log group, alarms, SNS topics
├── variables.tf     # log_group_name, alert_email, alb_arn, ecs_service_name, etc.
└── outputs.tf       # sns_topic_arns, log_group_name
```

## Resources
### CloudWatch Log Group
- Name: `/ecs/kinnoo-server-dev`
- Retention: 30 days

### CloudWatch Alarms
1. **ALB 5xx count**: Trigger when HTTPCode_ELB_5XX_Count > 10 in 5 minutes → SNS alert
2. **Unhealthy targets**: Trigger when UnHealthyHostCount > 0 for 2 consecutive checks → SNS alert
3. **ECS CPU utilization**: Trigger when CPUUtilization > 80% for 5 minutes → SNS alert

### SNS Topics
1. **kinnoo-dev-alerts** — Operational alerts (5xx, unhealthy, CPU). Email subscription for Jerry.
2. **kinnoo-dev-password-reset** — Password reset notifications. Email subscription for Jerry. Used by feature109 (forgot password endpoint sends to this topic).

## Implementation Notes
- Jerry's alert email comes from `terraform.tfvars` (e.g., `alert_email = "jerry@example.com"`)
- SNS email subscriptions require manual confirmation (AWS sends confirmation email)
- Password reset SNS topic ARN is passed to ECS task as environment variable
- Alarms use `aws_cloudwatch_metric_alarm` with `alarm_actions = [sns_topic_arn]`

## Dependencies
- feature103 (project structure)
- feature105 (ALB ARN, ECS cluster/service names for alarm dimensions)

## Acceptance Criteria Summary
1. CloudWatch log group with 30-day retention
2. Alarms for 5xx, unhealthy targets, high CPU
3. SNS topics for alerts and password reset
4. Email subscription (manual confirmation)
5. `terraform validate` passes
