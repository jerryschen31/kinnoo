# Task501 Notes

## Summary
- Added canonical provider-neutral auth env contract resolution in `server/config.py` with alias fallback support.
- Updated `server/auth/oidc.py` to load OIDC configuration from canonical auth keys first and fail fast on missing required fields.
- Updated CLI auth env loading (`src/kinnoo/auth_command.py`, `src/kinnoo/config.py`) to prefer canonical auth env names with transition aliases.
- Extended IaC secret outputs and ECS runtime secret wiring to include canonical `AUTH_*` keys while retaining transition aliases.
- Added runtime + IaC alignment coverage in `server/tests/test_config.py` and updated IaC alignment assertions.

## Teaching Notes
- Canonical key-first resolution avoids env drift and makes multi-provider auth migrations safer.
- Alias fallback should remain centralized and temporary to prevent long-term duplicate config contracts.
- IaC and app runtime contracts should be validated together in tests to catch deployment-time config mismatches early.
