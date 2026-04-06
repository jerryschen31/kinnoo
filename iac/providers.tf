provider "aws" {
  region = var.aws_region
  profile = "jerry"
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
