# task520 implementation notes

- `server/config.py`: removed the implicit production CORS fallback that defaulted to `("https://dev.kinnoo.ai", "https://dev-api.kinnoo.ai")`. Production mode now raises `ValueError("CORS_ORIGINS must be set in production (no implicit dev-domain fallback).")` if `CORS_ORIGINS` is missing or contains only whitespace. Dev mode is unchanged (still falls back to `("*",)`).
- Added `server/tests/test_feature121_production_config.py` (test743) covering: prod-without-CORS fails fast, prod-with-explicit-prod-origins succeeds, whitespace-only `CORS_ORIGINS` fails, and dev mode still keeps the permissive default.
- IaC env injection for `CORS_ORIGINS` is already wired through `module.ecs_fargate`'s task definition env block; no Terraform changes needed for the new contract — the operator must set `CORS_ORIGINS` in the prod tfvars/secrets path before apply (documented in the runbook for Phase 4).
