locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # Keep explicit secret names to make container injection predictable.
  ordered_secret_keys = ["JWT_SECRET", "SESSION_SECRET", "ADMIN_PASSWORD"]
  container_secrets = [
    for secret_key in local.ordered_secret_keys : {
      name      = secret_key
      valueFrom = var.secret_arns[secret_key]
    }
    if contains(keys(var.secret_arns), secret_key)
  ]
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/aws/ecs/${local.name_prefix}-server"
  retention_in_days = 30

  tags = var.tags
}

resource "aws_efs_file_system" "auth" {
  creation_token = "${local.name_prefix}-auth"
  encrypted      = true

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-efs"
  })
}

resource "aws_security_group" "efs" {
  name        = "${local.name_prefix}-efs-sg"
  description = "Allow NFS from ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
    description     = "ECS tasks to EFS"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_efs_mount_target" "auth" {
  count = length(var.subnet_ids)

  file_system_id  = aws_efs_file_system.auth.id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_access_point" "auth" {
  file_system_id = aws_efs_file_system.auth.id

  posix_user {
    uid = 1000
    gid = 1000
  }

  root_directory {
    path = "/data"

    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "0755"
    }
  }

  tags = var.tags
}

resource "aws_ecs_cluster" "this" {
  name = "${local.name_prefix}-cluster"

  tags = var.tags
}

resource "aws_ecs_task_definition" "app" {
  family                   = "${local.name_prefix}-server"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "kinnoo-server"
      image     = var.image_url
      essential = true
      portMappings = [
        {
          containerPort = var.container_port
          hostPort      = var.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "KINNOO_ENV"
          value = "production"
        },
        {
          name  = "REGISTRY_STORAGE_BACKEND"
          value = "s3"
        },
        {
          name  = "REGISTRY_S3_BUCKET"
          value = var.registry_bucket_name
        },
        {
          name  = "REGISTRY_S3_REGION"
          value = var.aws_region
        },
        {
          name  = "REGISTRY_LOCAL_STORAGE_ROOT"
          value = "/data/.registry-storage"
        },
        {
          name  = "S3_BUCKET"
          value = var.registry_bucket_name
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "SNS_TOPIC_ARN"
          value = var.sns_topic_arn
        }
      ]
      secrets = local.container_secrets
      mountPoints = [
        {
          sourceVolume  = "auth-data"
          containerPath = "/data"
          readOnly      = false
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  volume {
    name = "auth-data"

    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.auth.id
      root_directory     = "/"
      transit_encryption = "ENABLED"

      authorization_config {
        access_point_id = aws_efs_access_point.auth.id
        iam             = "ENABLED"
      }
    }
  }

  tags = var.tags
}

resource "aws_ecs_service" "app" {
  name            = "${local.name_prefix}-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [var.ecs_security_group_id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "kinnoo-server"
    container_port   = var.container_port
  }

  tags = var.tags
}
