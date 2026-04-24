# task521 implementation notes

- `iac/providers.tf` and `iac/state/main.tf`: removed `profile = "jerry"` from the AWS provider blocks. Region remains `var.aws_region`. Operators now supply credentials through the standard AWS credential chain (`AWS_PROFILE`, `AWS_ACCESS_KEY_ID`/`SECRET`, OIDC role assumption, etc.). Each provider block has an inline comment explaining the contract.
- Added `tests/iac/test_feature121_provider_portability.py` (test744): static parse asserting no `profile = "..."` literal remains and that region wiring is intact.
- Operator credential expectations are documented in the deployment runbook (Phase 0/1).
