# task518 implementation notes

- Added neutral domain inputs to `iac/variables.tf` (`base_domain`, `frontend_subdomain`, `api_subdomain`, `frontend_record_type`, `frontend_record_content`, `manage_frontend_record`); kept the legacy `dev_*` inputs as deprecated aliases so existing tfvars do not break.
- Computed `local.frontend_fqdn` and `local.api_fqdn` in `iac/locals.tf` from the new inputs and threaded `local.api_fqdn` into the ALB module (replacing the hardcoded `dev-api.kinnoo.ai` literal in `iac/main.tf`).
- Refactored `iac/modules/cloudflare/{main.tf,variables.tf}` to take `frontend_subdomain` / `api_subdomain` and to emit neutral `frontend_url` / `api_url` outputs (kept `dev_url` / `dev_api_url` as deprecated aliases). Removed hardcoded `dev_host` / `dev_api_host` literals.
- Removed the unsafe `default = "dev-api.kinnoo.ai"` from `iac/modules/alb/variables.tf` so a misconfigured tfvars cannot silently bind the prod ACM cert to the dev hostname.
- Updated `iac/environments/dev/terraform.tfvars` to use the new neutral inputs and added explicit `frontend_subdomain="dev"`, `api_subdomain="dev-api"`. Prod tfvars uses `www`/`api` (covered by task524).
- Added `tests/iac/test_feature121_env_isolation.py` (test741) which statically asserts root/module wiring no longer carries dev literals and that dev/prod tfvars surface distinct subdomains.
