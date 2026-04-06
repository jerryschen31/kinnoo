output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.this.dns_name
}

output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.this.arn
}

output "target_group_arn" {
  description = "Target group ARN for ECS service wiring"
  value       = aws_lb_target_group.ecs.arn
}

output "acm_arn" {
  description = "ACM certificate ARN"
  value       = aws_acm_certificate.api.arn
}

output "acm_validation_record" {
  description = "DNS validation CNAME record to publish in Cloudflare"
  value = {
    name  = one(aws_acm_certificate.api.domain_validation_options).resource_record_name
    type  = one(aws_acm_certificate.api.domain_validation_options).resource_record_type
    value = one(aws_acm_certificate.api.domain_validation_options).resource_record_value
    ttl   = 60
  }
}