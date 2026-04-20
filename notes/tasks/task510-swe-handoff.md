# Task510 SWE Handoff - kinnoo-server DB/Admin Command Surface

## Objective
Add server CLI DB/admin commands required for Postgres rollout operations.

## Deliverables
- Implement/extend: `kinnoo-server db migrate`, `kinnoo-server db seed`, and DB/admin query commands.
- Add domain read/admin commands for tenant/user/agent/audit inspection.
- Add tests for happy and failure paths.

## Task Contracts
- Commands must produce actionable operator output.
- DB failures/invalid input must return deterministic errors.
- Command behavior should be documented for operator usage.

## Validation
- Run command-level integration tests against Postgres test DB.
- Verify migration/seed plus representative read/admin workflows.
