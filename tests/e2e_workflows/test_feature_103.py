from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_feature103_group1() -> None:
    root_files = [
        "iac/versions.tf",
        "iac/providers.tf",
        "iac/variables.tf",
        "iac/outputs.tf",
        "iac/locals.tf",
        "iac/main.tf",
    ]

    for file_path in root_files:
        assert Path(file_path).exists(), f"missing required root file: {file_path}"

    backend_tf = _read("iac/backend.tf")
    assert 'backend "s3"' in backend_tf
    assert 'bucket       = "kinnoo-terraform-state-dev"' in backend_tf
    assert "use_lockfile = true" in backend_tf

    state_main = _read("iac/state/main.tf")
    assert "aws_s3_bucket" in state_main
    assert "aws_s3_bucket_versioning" in state_main

    vpc_main = _read("iac/modules/vpc/main.tf")
    assert "us-west-2a" in vpc_main or '${var.aws_region}a' in vpc_main
    assert "us-west-2b" in vpc_main or '${var.aws_region}b' in vpc_main
    assert 'from_port   = 443' in vpc_main
    assert "cloudflare_ipv4_cidrs" in vpc_main
    assert "from_port       = 8000" in vpc_main


def test_feature103_group2() -> None:
    vpc_main = _read("iac/modules/vpc/main.tf")
    assert "aws_vpc_endpoint" in vpc_main
    assert "service_name" in vpc_main
    assert "s3" in vpc_main.lower()

    # Guardrail for AC6: no NAT resources should be declared for dev/beta.
    assert "aws_nat_gateway" not in vpc_main

    tfvars = Path("iac/environments/dev/terraform.tfvars")
    assert tfvars.exists(), "iac/environments/dev/terraform.tfvars must exist"
    tfvars_text = tfvars.read_text(encoding="utf-8")
    assert "aws_region" in tfvars_text and "us-west-2" in tfvars_text
    assert "environment" in tfvars_text and '"dev"' in tfvars_text

    versions = _read("iac/versions.tf")
    assert "required_version" in versions
    assert "required_providers" in versions
