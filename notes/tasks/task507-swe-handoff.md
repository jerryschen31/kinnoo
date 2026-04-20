# Task507 SWE Handoff - Server Database Runtime, Schema, and Alembic

## Objective
Create `server/database/` with async session runtime, 8-table schema models, repository layer, exceptions, and Alembic async migration setup.

## Required Files
- `server/database/session.py`
- `server/database/models/*.py`
- `server/database/repository.py`
- `server/database/exceptions.py`
- `server/database/migrations/*`
- update `server/config.py`

## Task Contracts
- Tables: users, tenants, tenant_members, agents, agent_versions, api_keys, audit_log, download_events.
- Include relationship and index definitions for hot read paths.
- Provide repository APIs (no route-level SQL leakage).
- Alembic must support async env and reliable upgrade/downgrade cycle.

## Validation
- Run migration cycle tests (upgrade/downgrade/upgrade).
- Run schema/repository integration tests in Postgres-backed fixtures.
