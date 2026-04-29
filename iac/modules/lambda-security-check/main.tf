locals {
  lambda_name = "${var.project_name}-${var.environment}-security-check"
}

resource "aws_cloudwatch_log_group" "security_check" {
  name              = "/aws/lambda/${local.lambda_name}"
  retention_in_days = 30

  tags = var.tags
}

resource "aws_lambda_function" "security_check" {
  function_name = local.lambda_name
  role          = var.lambda_role_arn
  package_type  = "Image"
  image_uri     = var.image_uri
  timeout       = 120

  environment {
    variables = {
      KINNOO_SECURITY_CHECK_MODE     = "lambda"
      KINNOO_SECURITY_RESULTS_PREFIX = "security-check/tenants"
    }
  }

  tags = var.tags
}

resource "aws_lambda_permission" "allow_registry_s3_invoke" {
  statement_id  = "AllowExecutionFromRegistryS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.security_check.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.registry_bucket_arn
}

resource "aws_s3_bucket_notification" "registry_publish_events" {
  bucket = var.registry_bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.security_check.arn
    events              = ["s3:ObjectCreated:Put", "s3:ObjectCreated:CompleteMultipartUpload", "s3:ObjectCreated:Copy"]
    filter_prefix       = "archives/tenants/"
    filter_suffix       = ".kno"
  }

  depends_on = [aws_lambda_permission.allow_registry_s3_invoke]
}
