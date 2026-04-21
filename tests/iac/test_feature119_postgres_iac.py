from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_feature119_test721_private_rds_posture() -> None:
    module_main = _read("iac/modules/rds-postgres/main.tf")
    vpc_main = _read("iac/modules/vpc/main.tf")
    root_main = _read("iac/main.tf")
    assert 'publicly_accessible          = false' in module_main
    assert "storage_encrypted            = true" in module_main
    assert "multi_az                     = local.is_prod" in module_main
    assert "deletion_protection          = local.is_prod" in module_main
    assert 'from_port       = 5432' in vpc_main
    assert 'security_groups = [aws_security_group.ecs.id]' in vpc_main
    assert 'module "rds_postgres"' in root_main
    assert "private_subnet_ids              = module.vpc.private_subnet_ids" in root_main


def test_feature119_test722_ecs_env_secret_wiring() -> None:
    ecs_main = _read("iac/modules/ecs-fargate/main.tf")
    secrets_main = _read("iac/modules/secrets/main.tf")
    assert '"REGISTRY_DATABASE_URL"' in ecs_main
    assert '"REGISTRY_METADATA_BACKEND"' in ecs_main
    assert '"REGISTRY_DB_POOL_SIZE"' in ecs_main
    assert '"REGISTRY_DB_MAX_OVERFLOW"' in ecs_main
    assert '"REGISTRY_DB_POOL_RECYCLE_SECONDS"' in ecs_main
    assert "REGISTRY_DATABASE_URL" in secrets_main
