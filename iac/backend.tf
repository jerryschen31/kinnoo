terraform {
  backend "s3" {
    # Environment-specific backend settings are provided via:
    # terraform init -reconfigure -backend-config=environments/<env>/backend.hcl
  }
}
