# Task501 SWE Handoff - Provider-Neutral Config and IaC Alignment

## Objective
Make provider-neutral auth env keys canonical in runtime and align IaC env/secret injection to those names.

## Contract
- Canonical keys use provider-neutral naming.
- Kinde-prefixed names are optional compatibility aliases only.
- Missing required config fails fast with clear startup errors.

## Primary Files
- `server/config.py`
- `iac/modules/ecs-fargate/main.tf`
- `iac/modules/secrets/main.tf`
- `iac/environments/dev/terraform.tfvars`

## Required Tests
- `test713`

## Execution Guidance
1. Resolve config aliases centrally in config loading.
2. Update IaC mappings so runtime no longer depends on legacy mismatched names.
3. Run:
   - `python3 scripts/validate_project_manifests.py`
   - `python3 -m pytest server/tests -q -k "config and feature118"`
