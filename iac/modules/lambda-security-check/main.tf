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
  timeout       = 60

  environment {
    variables = {
      KINNOO_SECURITY_CHECK_MODE = "lambda"
    }
  }

  tags = var.tags
}
