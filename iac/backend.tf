terraform {
  backend "s3" {
    bucket       = "kinnoo-terraform-state-dev"
    key          = "dev/network/terraform.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true
  }
}
