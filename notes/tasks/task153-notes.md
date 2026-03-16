# Task153 - feature25 AC coverage and no-services regression gate

## Summary
- Implemented feature25 regression coverage in `tests/test_regression_v1.py` with two task153-targeted tests:
  - `test_feature25_no_services_regression_unchanged` (test235)
  - `test_feature25_ac_coverage_and_no_services_regression_gate`
- Added a no-services fixture run regression that validates:
  - one-shot execution still succeeds for manifests without `services`,
  - no service-health section is emitted for no-services manifests.
- Added a feature25 AC coverage regression gate that executes the full mapped test set:
  - test228, test229, test230, test231, test232, test233, test234, test235.
- Updated `tests/test_cli.py::test_feature25_run_checks_all_declared_services_before_entrypoint` to align with task152 fail-fast policy by using a healthy process-check fixture and pass-path assertions.

## Tests and results
- `python3 -m pytest tests/test_regression_v1.py::test_feature25_no_services_regression_unchanged tests/test_regression_v1.py::test_feature25_ac_coverage_and_no_services_regression_gate` -> `2 passed`

## Bug/error notes
- Encountered two issues while wiring task153 regression coverage:
  - no-services fixture had an f-string quoting bug in generated `run.py`.
  - existing feature25 run test expected guidance text even after converting all checks to healthy pass-path.
- Both were resolved with targeted test fixes.
- Repeated bug/error class cap status: no repeated class exceeded the 5-attempt limit.

## Teaching notes
- A regression gate should compose acceptance tests, but each constituent test must remain semantically aligned with newer policy changes (task152 changed the non-interactive behavior contract).
- For compatibility checks, explicit no-services fixtures are high-value because they protect legacy users from additive feature regressions.
- In agentic runtime systems, separating pass-path vs fail-path assertions avoids brittle tests and makes contract intent clearer during staged rollouts.
