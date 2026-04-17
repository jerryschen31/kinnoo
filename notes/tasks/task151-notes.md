# Task151 - feature25 integrate service checks into run and preflight output

## Summary
- Integrated feature25 service checks into both execution paths in `src/kinnoo/run_command.py`.
- Added service-check orchestration helpers:
  - `_load_declared_services(manifest)`
  - `_run_service_checks(manifest)`
  - `_render_service_check_for_preflight(result)`
  - `_render_service_check_for_run(result)`
- `kinnoo run --preflight` now includes a `Service health checks:` section (when services are declared) with deterministic per-service PASS/FAIL lines, including service name, service type, method, and guidance on failure.
- `kinnoo run` now executes and renders all declared service checks before entrypoint execution.
- Added flush behavior for run-path service-check output to preserve deterministic ordering before entrypoint output under captured stdout conditions.

## Tests added/updated for task151
- Added `tests/test_cli.py::test_feature25_run_checks_all_declared_services_before_entrypoint` (test231):
  - verifies all declared services are checked pre-entrypoint in `run` mode,
  - verifies output includes service name/type/method and guidance for failure,
  - verifies entrypoint still executes in this task scope.
- Added `tests/test_run_preflight.py::test_feature25_preflight_includes_service_health_results` (test232):
  - verifies preflight output includes service health section and service-level results,
  - verifies preflight does not execute entrypoint,
  - verifies unhealthy service contributes to preflight FAIL readiness outcome.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_feature25_run_checks_all_declared_services_before_entrypoint tests/test_run_preflight.py::test_feature25_preflight_includes_service_health_results` -> `2 passed`
- `python3 scripts/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Bug/error notes
- Encountered one repeated issue class: stream-order assertion instability due stdout buffering when parent and child process outputs are captured.
- Resolution:
  - made run-path service-check prints flush immediately,
  - kept assertion robust while still checking expected pre-entrypoint behavior.
- Same bug/error class fix attempts: `2` (below cap of 5).

## Teaching notes
- This task demonstrates a strong separation between capability and policy:
  - task150 provides checker primitives,
  - task151 integrates and reports checks,
  - task152 will enforce interactive/non-interactive failure policy.
- Deterministic output in process orchestration often requires explicit flushes; without this, logical execution order can appear inverted in captured logs.
- For agentic runtime design, stable structured tool outputs plus deterministic rendering creates a reliable substrate for future policy layers (prompts, fail-fast rules, retries).
