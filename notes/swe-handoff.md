# SWE Handoff — Feature9 (Manifest Schema V2 Extensions)

## Scope
Implement feature9 across tasks `task48`–`task52` and tests `test71`–`test77`.

## Ordered implementation plan
1. `task48` — Extend schema for optional V2 fields (`description`, `author`, `license`, `env_vars`).
2. `task49` — Add validator checks for optional-field types and `env_vars` list/non-empty string rules.
3. `task50` — Ensure V1 manifest compatibility remains unchanged.
4. `task51` — Update `kinnoo init` templates to include `description` + `author` placeholders.
5. `task52` — Update schema docs and README for feature9 field semantics.

## Task → tests mapping
- `task48`: `test71`, `test72`
- `task49`: `test72`, `test74`, `test76`
- `task50`: `test73`
- `task51`: `test75`
- `task52`: `test77`

## Files expected to change
- `src/kinnoo/schema.py`
- `src/kinnoo/validator.py`
- `src/kinnoo/templates.py`
- `src/kinnoo/init_command.py`
- `docs/manifest-schema-reference.md`
- `README.md`
- `tests/test_validator.py`
- `tests/test_init.py`
- `tests/test_docs.py` (if not present, create)

## Design constraints
- New fields are optional only; do not break V1 manifests.
- Keep validator error strings stable and specific (tests assert text).
- `env_vars` must validate as `list[str]` with non-empty items.
- No changes to runtime behavior in this feature; schema + validation + templates + docs only.

## SWE completion checklist
- Implement tasks in order and keep changes scoped.
- Add/implement `test71`–`test77` exactly per automation paths in `TESTS.txt`.
- Run:
	- `python3 -m pytest tests/test_validator.py tests/test_init.py tests/test_docs.py`
	- `python3 src/validate_project_manifests.py`
- Update task statuses to `in-progress` then `needs-review` when ready for TechLead review.
