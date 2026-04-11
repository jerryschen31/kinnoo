data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "ecs_task_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task" {
  name               = "${var.project_name}-${var.environment}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "ecs_task_permissions" {
  statement {
    sid = "RegistryBucketAccess"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    resources = [
      var.registry_bucket_arn,
      "${var.registry_bucket_arn}/*",
    ]
  }
}

data "aws_iam_policy_document" "ecs_task_lambda_invoke" {
  statement {
    sid = "InvokeSecurityCheckLambda"

    actions = [
      "lambda:InvokeFunction",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_task_s3" {
  name   = "${var.project_name}-${var.environment}-ecs-task-s3"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task_permissions.json
}

resource "aws_iam_role_policy" "ecs_task_lambda_invoke" {
  name   = "${var.project_name}-${var.environment}-ecs-task-lambda-invoke"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.ecs_task_lambda_invoke.json
}

resource "aws_iam_role" "ecs_execution" {
  name               = "${var.project_name}-${var.environment}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_security_check" {
  name               = "${var.project_name}-${var.environment}-lambda-security-check-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "lambda_security_check_permissions" {
  statement {
    sid = "CloudWatchLogsWrite"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:CreateLogGroup",
    ]

    resources = ["*"]
  }

  statement {
    sid = "RegistryBucketReadWrite"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]

    resources = [
      var.registry_bucket_arn,
      "${var.registry_bucket_arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_security_check" {
  name   = "${var.project_name}-${var.environment}-lambda-security-check-policy"
  role   = aws_iam_role.lambda_security_check.id
  policy = data.aws_iam_policy_document.lambda_security_check_permissions.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution_default" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ecs_execution_extras" {
  statement {
    sid = "EcrRead"

    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
      "ecr:GetAuthorizationToken",
    ]

    resources = ["*"]
  }

  statement {
    sid = "CloudWatchLogsWrite"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["*"]
  }

  statement {
    sid = "SecretsRead"

    actions = [
      "secretsmanager:GetSecretValue",
      "kms:Decrypt",
    ]

    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "ecs_execution_extras" {
  name   = "${var.project_name}-${var.environment}-ecs-execution-extras"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.ecs_execution_extras.json
}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
  ]

  tags = var.tags
}

data "aws_iam_policy_document" "github_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "${var.project_name}-${var.environment}-github-actions-role"
  assume_role_policy = data.aws_iam_policy_document.github_assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "github_actions_permissions" {
  statement {
    sid = "EcrPushAndPull"

    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:CompleteLayerUpload",
      "ecr:GetAuthorizationToken",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]

    resources = ["*"]
  }

  statement {
    sid = "EcsDeploy"

    actions = [
      "ecs:DescribeServices",
      "ecs:DescribeTaskDefinition",
      "ecs:RegisterTaskDefinition",
      "ecs:UpdateService",
    ]

    resources = ["*"]
  }

  statement {
    sid = "TerraformStateBucket"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket",
    ]

    resources = [
      "arn:aws:s3:::kinnoo-terraform-state-dev",
      "arn:aws:s3:::kinnoo-terraform-state-dev/*",
    ]
  }
}

resource "aws_iam_role_policy" "github_actions" {
  name   = "${var.project_name}-${var.environment}-github-actions-policy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_actions_permissions.json
}

output "ecs_task_role_arn" {
  description = "ARN for ECS task role"
  value       = aws_iam_role.ecs_task.arn
}

output "ecs_execution_role_arn" {
  description = "ARN for ECS execution role"
  value       = aws_iam_role.ecs_execution.arn
}

output "github_actions_role_arn" {
  description = "ARN for GitHub Actions OIDC role"
  value       = aws_iam_role.github_actions.arn
}

output "lambda_security_check_role_arn" {
  description = "ARN for security-check Lambda execution role"
  value       = aws_iam_role.lambda_security_check.arn
}
