from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_feature104_group1() -> None:
    module_main = _read("iac/modules/s3-registry/main.tf")
    module_vars = _read("iac/modules/s3-registry/variables.tf")

    assert 'resource "aws_s3_bucket" "registry"' in module_main
    assert 'sse_algorithm = "AES256"' in module_main
    assert 'mode = "GOVERNANCE"' in module_main
    assert 'status = "Enabled"' in module_main
    assert 'resource "aws_s3_bucket_public_access_block" "registry"' in module_main

    assert 'variable "bucket_name"' in module_vars
    assert 'variable "environment"' in module_vars


def test_feature104_group2() -> None:
    iam_main_path = Path("iac/modules/iam/main.tf")
    iam_vars_path = Path("iac/modules/iam/variables.tf")

    assert iam_main_path.exists(), "task420 must create iac/modules/iam/main.tf"
    assert iam_vars_path.exists(), "task420 must create iac/modules/iam/variables.tf"

    iam_main = iam_main_path.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role" "ecs_task"' in iam_main
    assert 'resource "aws_iam_role" "ecs_execution"' in iam_main
    assert 'resource "aws_iam_openid_connect_provider" "github"' in iam_main


def test_feature104_group3() -> None:
    secrets_main_path = Path("iac/modules/secrets/main.tf")
    secrets_vars_path = Path("iac/modules/secrets/variables.tf")

    assert secrets_main_path.exists(), "task421 must create iac/modules/secrets/main.tf"
    assert secrets_vars_path.exists(), "task421 must create iac/modules/secrets/variables.tf"

    secrets_main = secrets_main_path.read_text(encoding="utf-8")
    assert 'JWT_SECRET' in secrets_main
    assert 'SESSION_SECRET' in secrets_main
    assert 'ADMIN_PASSWORD' in secrets_main
