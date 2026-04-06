from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_feature105_group1() -> None:
    ecr_main = _read("iac/modules/ecr/main.tf")
    alb_main = _read("iac/modules/alb/main.tf")

    assert 'resource "aws_ecr_repository" "server"' in ecr_main
    assert "scan_on_push = true" in ecr_main
    assert 'resource "aws_ecr_lifecycle_policy" "server"' in ecr_main

    assert 'resource "aws_lb" "this"' in alb_main
    assert 'resource "aws_lb_listener" "https"' in alb_main
    assert "port              = 443" in alb_main
    assert 'resource "aws_acm_certificate" "api"' in alb_main
    assert 'validation_method = "DNS"' in alb_main
    assert 'path                = "/health"' in alb_main


def test_feature105_group2() -> None:
    ecs_main_path = Path("iac/modules/ecs-fargate/main.tf")
    ecs_vars_path = Path("iac/modules/ecs-fargate/variables.tf")

    assert ecs_main_path.exists(), "task423 must create iac/modules/ecs-fargate/main.tf"
    assert ecs_vars_path.exists(), "task423 must create iac/modules/ecs-fargate/variables.tf"

    ecs_main = ecs_main_path.read_text(encoding="utf-8")

    assert 'resource "aws_ecs_cluster" "this"' in ecs_main
    assert 'resource "aws_ecs_task_definition" "app"' in ecs_main
    assert 'cpu                      = 512' in ecs_main
    assert 'memory                   = 1024' in ecs_main
    assert "efs_volume_configuration" in ecs_main
    assert "secrets =" in ecs_main
    assert 'resource "aws_ecs_service" "app"' in ecs_main


def test_feature105_group3() -> None:
    ecs_main = _read("iac/modules/ecs-fargate/main.tf")
    ecs_vars = _read("iac/modules/ecs-fargate/variables.tf")

    assert 'resource "aws_efs_file_system" "auth"' in ecs_main
    assert 'resource "aws_efs_mount_target" "auth"' in ecs_main
    assert 'desired_count   = var.desired_count' in ecs_main
    assert 'variable "desired_count"' in ecs_vars
    assert 'default     = 1' in ecs_vars