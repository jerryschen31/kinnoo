# 🍊 Kinnoo Database & Persistence Rules (`db.rules.md`)

## 🎯 Core Philosophy
The database is the **Permanent Ledger** of Kinnoo. Every record must be treated as audit-grade data. We prioritize **Type Safety (Rigor)**, **Async execution (Performance)**, and **Migration Integrity (Longevity)**.

---

## 🛠️ The Tech Stack
- **Engine:** SQLAlchemy 2.0 (Core & ORM)
- **Model Layer:** SQLModel (Pydantic + SQLAlchemy synergy)
- **Migration:** Alembic
- **Driver:** `asyncpg` (PostgreSQL)

---

## 📂 Structural Organization
All database code must reside in `server/database/`:
- `models/`: One file per domain (e.g., `agent.py`, `user.py`, `audit.py`).
- `migrations/`: Alembic environment and versions.
- `session.py`: Async engine and session factory logic.
- `repository.py`: Data access patterns (The "Unit of Work").

---

## 📜 Mandatory Patterns (Adopt These)

### 1. The "Base" Rigor
Every table model must inherit from `SQLModel` and include:
- **UUID Primary Keys:** Use `uuid7` (time-ordered) for performance and security. No serial integers.
- **Audit Timestamps:** Every record must have `created_at` and `updated_at` (UTC).
- **Metadata:** Use `Sa.Column(JSONB)` for flexible, non-indexed metadata to ensure longevity as agent specs evolve.

### 2. Async-First Interaction
All DB calls must be `async`. Never use synchronous sessions which block the event loop.
- **Pattern:** Use the `AsyncSession` context manager or FastAPI dependency injection.

### 3. Explicit Relationship Loading
- **Pattern:** Always specify `lazy="selectin"` or `lazy="joined"` in relationships to avoid the dreaded "Lazy Initialization" errors in async contexts.
- **Rigor:** Be explicit. Do not rely on SQLAlchemy defaults.

### 4. The Repository Pattern
Do not leak DB logic into CLI or Web routes. 
- **Pattern:** Create a repository class for each entity.
  - *Example:* `AgentRepository.get_by_id(session, id)` instead of calling `session.exec(...)` in the UI layer.



---

## 🚫 Anti-Patterns (Avoid These)

| Anti-Pattern | Why it fails | The Kinnoo Way |
| :--- | :--- | :--- |
| **Raw SQL Strings** | Vulnerable to injection; breaks Rigor. | Use **SQLModel / SQLAlchemy Expression Language**. |
| **N+1 Querying** | Kills scalability during Registry search. | Use `selectinload` for collections. |
| **Circular Imports** | Common in model relationships. | Use **String Forward References** for type hints. |
| **Generic Exceptions** | Hard to debug in production. | Define custom DB exceptions (e.g., `RegistryEntryNotFoundError`). |
| **Commit in Loops** | Causes massive performance overhead. | Batch operations; commit once per transaction. |

---

## 🏗️ Alembic Migration Workflow

Migrations are the **History of Kinnoo**. They must be treated with the same care as production code.

1. **Naming:** Every migration must have a descriptive slug: `alembic revision --autogenerate -m "add_kill_switch_to_agents"`.
2. **Manual Review:** Never trust `--autogenerate` blindly. The SWE agent **must** review the generated Python file to ensure types and constraints (Unique, Index) are correct.
3. **The "Non-Destructive" Rule:** Never use `DROP COLUMN` in a single-step migration if it contains production data. Use a three-step migration (Add New -> Sync Data -> Drop Old).
4. **Data Migrations:** Keep data-fixing scripts separate from schema-change scripts.

---

## 🍊 The "Verified 🍊" DB Check
Before an SWE agent finishes a DB task, it must verify:
- [ ] Is every field strictly typed (including `Optional` vs `Required`)?
- [ ] Are indexes added to frequently searched fields (e.g., `agent_name`, `author_id`)?
- [ ] Is there an Alembic script generated and tested?
- [ ] Does the `updated_at` trigger work?

***

### 💡 Guidance for the SWE Agent
> *"When you implement a new table, first define the Pydantic-compatible SQLModel. Ensure that sensitive fields (like API keys) are never included in the default 'Public' schema. If you are changing a schema, immediately run a migration test in the local Docker environment to ensure no data loss."*

**Would you like me to draft a specific `AuditLog` model following these rules so the Tech Lead can use it as a 'Gold Standard' template?** 🍊
