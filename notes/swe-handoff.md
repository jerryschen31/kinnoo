## SWE Handoff - Feature24 Service Declarations (Schema)

### Context
- Feature: feature24 "Service Declarations - Manifest Schema"
- Goal: add optional `services` manifest schema support and validator/inspect behavior.
- Scope: schema + validator + inspect output only. Runtime health-check execution is feature25.

### Tasks To Implement (Ordered)
1. `task146` - schema constants and manifest shape support
2. `task147` - validator enforcement for services objects, methods, and duplicates
3. `task148` - inspect output for declared services
4. `task149` - AC coverage + targeted regression gate

### Dependency Chain
- `task146` -> `task147` -> `task148` -> `task149`

### Design Constraints
- Keep feature24 schema-only. Do not add runtime health-check execution logic in run flow.
- Add schema constants in `src/kinnoo/schema.py`:
	- `SUPPORTED_SERVICE_TYPES`
	- `SUPPORTED_HEALTH_CHECK_METHODS`
- Preserve backward compatibility: manifests without `services` must continue to pass unchanged.
- Validation errors must be explicit and actionable, and include allowed values for invalid enums.
- Duplicate `services[].name` values must fail validation deterministically.
- `kinnoo inspect` output must stay human-readable and include services data only when declared.

### Files Expected To Change
- `src/kinnoo/schema.py`
- `src/kinnoo/validator.py`
- `src/kinnoo/inspect_command.py`
- `tests/test_validator.py`
- `tests/test_cli_inspect.py`
- Optional regression touchpoint: `tests/test_regression_v1.py` (if needed for explicit no-services guard)

### AC-to-Test Mapping
- AC1 -> `test222`
- AC2 -> `test223`
- AC3 -> `test224`
- AC4 -> `test223`, `test224`
- AC5 -> `test225`
- AC6 -> `test226`
- AC7 -> `test227`

### Suggested Implementation Notes
- Validate `services` as list of objects.
- For each service:
	- required fields: `name`, `type`
	- `type` in allowed service types
	- optional `health_check` object
	- when `health_check.method` is set:
		- `tcp` requires `port`
		- `http` requires `url`
		- `process` requires `process_name`
- Keep error path names specific (for example, service index + field path) so debugging is easy.

### Validation Commands (SWE)
- `python3 src/validate_project_manifests.py`
- `python3 -m pytest tests/test_validator.py -k feature24`
- `python3 -m pytest tests/test_cli_inspect.py -k feature24`
- `python3 -m pytest` (final regression gate)

### Done Criteria
- All feature24 ACs covered by automated tests (`test222`-`test227`).
- Manifest validator passes with updated FEATURES/TASKS/TESTS references.
- No regressions for manifests without `services`.
