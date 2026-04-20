provider "aws" {
  region  = var.aws_region
  profile = "jerry"
}

provider "cloudflare" {
  # API token is supplied via CLOUDFLARE_API_TOKEN in the shell environment.
}
