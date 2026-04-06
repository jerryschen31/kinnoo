resource "aws_s3_bucket" "registry" {
  bucket              = var.bucket_name
  object_lock_enabled = true

  tags = merge(var.tags, {
    Name        = var.bucket_name
    Environment = var.environment
  })
}

resource "aws_s3_bucket_server_side_encryption_configuration" "registry" {
  bucket = aws_s3_bucket.registry.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "registry" {
  bucket = aws_s3_bucket.registry.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_object_lock_configuration" "registry" {
  bucket = aws_s3_bucket.registry.id

  rule {
    default_retention {
      mode = "GOVERNANCE"
      days = 30
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "registry" {
  bucket = aws_s3_bucket.registry.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

resource "aws_s3_bucket_public_access_block" "registry" {
  bucket = aws_s3_bucket.registry.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_name" {
  description = "Registry bucket name"
  value       = aws_s3_bucket.registry.bucket
}

output "bucket_arn" {
  description = "Registry bucket ARN"
  value       = aws_s3_bucket.registry.arn
}
