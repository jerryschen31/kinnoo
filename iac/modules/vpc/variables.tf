variable "aws_region" {
  description = "AWS region where VPC resources are created"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "project_name" {
  description = "Project name used in naming"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "Two CIDR blocks for public subnets"
  type        = list(string)
}

variable "cloudflare_ipv4_cidrs" {
  description = "Cloudflare IPv4 ranges allowed on ALB HTTPS"
  type        = list(string)
  default = [
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22"
  ]
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
