aws_region          = "us-west-2"
environment         = "dev"
project_name        = "kinnoo"
vpc_cidr            = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
dev_record_type     = "AAAA"
dev_record_content  = "100::"
manage_dev_record   = false
# Set this to the pushed Lambda image URI from your account ECR.
# Example: 123456789012.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-lambda-security-check:v1
lambda_security_check_image_uri = "386775099533.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-lambda-security-check:v2"
