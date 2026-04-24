"""task524 / test747: prod tfvars completeness contract."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VARIABLES_TF = ROOT / "iac" / "variables.tf"
PROD_TFVARS = ROOT / "iac" / "environments" / "prod" / "terraform.tfvars"


_VAR_BLOCK = re.compile(
    r'variable\s+"(?P<name>[A-Za-z_][A-Za-z0-9_]*)"\s*\{(?P<body>[^}]*?)\}',
    re.DOTALL,
)


def _required_variables() -> list[str]:
    """Return the list of root-module variables that have no default OR are
    explicitly nullable=false. Those are the variables an operator MUST set
    in tfvars (or via -var) for `terraform apply` to succeed."""
    text = VARIABLES_TF.read_text(encoding="utf-8")
    required: list[str] = []
    for match in _VAR_BLOCK.finditer(text):
        name = match.group("name")
        body = match.group("body")
        has_default = re.search(r"^\s*default\s*=", body, re.MULTILINE) is not None
        is_nullable_false = re.search(r"nullable\s*=\s*false", body) is not None
        if (not has_default) or is_nullable_false:
            required.append(name)
    return required


def _parse_tfvars(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


@pytest.mark.regression_integration
@pytest.mark.docs_contract
def test_feature121_test747_prod_tfvars_required_keys() -> None:
    required = _required_variables()
    assert required, "expected to discover at least one required variable"

    prod_values = _parse_tfvars(PROD_TFVARS)

    missing = [name for name in required if name not in prod_values]
    assert not missing, (
        f"prod tfvars is missing required variables: {missing}. "
        "Add explicit values in iac/environments/prod/terraform.tfvars."
    )

    # Every prod value should be non-empty.
    for name in required:
        value = prod_values[name].strip().strip('"')
        assert value, f"prod tfvars value for {name!r} is empty"

    # Specifically validate the lambda image URI regex declared in variables.tf.
    image_uri = prod_values["lambda_security_check_image_uri"].strip('"')
    pattern = re.compile(
        r"^[0-9]{12}\.dkr\.ecr\.[a-z0-9-]+\.amazonaws\.com\/.+:.+$"
    )
    assert pattern.match(image_uri), (
        f"lambda_security_check_image_uri={image_uri!r} does not match the "
        "pattern declared in iac/variables.tf"
    )

    # And the auth_provider must be explicitly declared.
    assert "auth_provider" in prod_values
    assert prod_values["auth_provider"].strip('"') in {"oidc_kinde", "legacy"}
