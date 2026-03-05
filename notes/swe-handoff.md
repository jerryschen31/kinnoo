# SWE Handoff — Feature12 Local Registry

## Scope
Implement feature12: local registry support for publish/install/list/search with backend abstraction for future remote registry support.

## Implementation Order (recommended)
1. `task69` — Define registry abstraction and local backend
2. `task70` — Add publish command parsing and CLI wiring
3. `task71` — Implement publish metadata extraction and copy flow
4. `task72` — Parse install registry spec while preserving file install
5. `task73` — Implement registry version resolution rules
6. `task74` — Integrate registry resolution into install flow
7. `task75` — Add local registry list command
8. `task76` — Add local registry search command
9. `task77` — Document local registry commands and behavior

## Task → Test ID Mapping (exact)
- `task69` → `test96`
- `task70` → `test97`
- `task71` → `test98`
- `task72` → `test99`
- `task73` → `test100`
- `task74` → `test101`
- `task75` → `test102`
- `task76` → `test103`
- `task77` → `test104`

## Key Design Constraints
- Keep publish/resolve/list/search behavior behind a registry backend abstraction (`feature12` AC9).
- Preserve existing `kinnoo install <file.kno>` behavior while adding `<name>` and `<name>==<version>` selectors (AC8).
- For version resolution logic, ensure deterministic ordering and test fixtures with multiple versions of the same agent (AC3/AC4).
- Duplicate publish for same `name+version` must fail clearly with no silent overwrite (AC7).
- Keep CLI output deterministic where tests assert user-visible messages and listings.

## Files Expected to Change
- `src/kinnoo/cli.py`
- `src/kinnoo/install_command.py`
- `src/kinnoo/publish_command.py`
- `src/kinnoo/list_command.py`
- `src/kinnoo/search_command.py`
- `src/kinnoo/registry.py`
- `src/kinnoo/registry_backends.py`
- `README.md`
- `docs/manifest-schema-reference.md`

## Definition of Done
- Tasks `task69`–`task77` moved to `needs-review` by SWE after implementation.
- Tests `test96`–`test104` implemented and passing.
- `python3 src/validate_project_manifests.py` passes after any manifest edits.
