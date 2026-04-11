aws_region          = "us-west-2"
environment         = "dev"
project_name        = "kinnoo"
vpc_cidr            = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
dev_record_type     = "AAAA"
dev_record_content  = "100::"
manage_dev_record   = false
