provider "aws" {
  region = var.aws_region
  # Operator credentials are resolved from the standard AWS credential chain
  # (AWS_PROFILE, AWS_ACCESS_KEY_ID/SECRET, OIDC role assumption, etc.).
  # Do not hardcode a `profile` here so the same Terraform root is portable
  # across operators and CI environments. See task521 / notes/prod-deployment-instructions.md
  # Phase 0 for the expected operator credential setup.
}

provider "cloudflare" {
  # API token is supplied via CLOUDFLARE_API_TOKEN in the shell environment.
}
