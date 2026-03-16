## Tech Lead Review

### Findings (ordered by severity)

1. High: Feature24 AC enum contract does not match implementation and tests.
- Feature24 AC2/AC4 define allowed service types as: `mcp-server`, `vector-db`, `database`, `api`, `local-process`.
- Implementation currently allows: `postgres`, `redis`, `http-api`, `process` in `src/kinnoo/schema.py` (`SUPPORTED_SERVICE_TYPES`).
- Validator and tests are aligned to implementation (for example, `tests/test_validator.py` and `tests/test_cli_inspect.py`) but not aligned to feature AC text in `FEATURES.txt`.
- Impact: feature appears green in tests but does not satisfy documented acceptance criteria as written.

2. Medium: Health-check method requirement is not explicitly enforced when `health_check` object exists.
- AC3 language describes `health_check` object with `method` and method-specific fields.
- Validator enforces method-specific fields only when `method` equals a recognized value; it does not require `method` to exist when a `health_check` object is present.
- Impact: ambiguous/partial schema acceptance; malformed `health_check: {port: 5432}` can avoid intended constraint.

3. Process consistency: Feature status in manifests is not advanced for review-ready state.
- `task146`-`task149` are `needs-review` in `TASKS.txt`, but `feature24` remains `not-started` in `FEATURES.txt`.
- Impact: planning metadata drift (not a runtime blocker, but confusing for release governance).

### AC Coverage Assessment
- AC1: Covered by `test222` (services optional list acceptance).
- AC2: Covered by `test223` (required fields + service type validation), but blocked by enum mismatch against AC text.
- AC3: Partially covered by `test224`; method-specific fields are covered. Missing explicit test/assertion that `health_check.method` is required when `health_check` exists.
- AC4: Covered by `test223` + `test224` for invalid type/method handling, but enum mismatch against AC text remains.
- AC5: Covered by `test225` and validator no-services regression behavior.
- AC6: Covered by `test226` for inspect output rendering of services.
- AC7: Covered by `test227` duplicate service-name validation.

### Full Regression Result
- Command: `python3 -m pytest`
- Result: `222 passed, 1 skipped`
- Assessment: no cross-feature runtime regressions detected.

### Recommendation Before Merge
- Do not merge yet.
- Required fixes:
  1. Resolve canonical service-type vocabulary mismatch (either update AC text in `FEATURES.txt` to the implemented taxonomy, or refactor implementation/tests to match AC taxonomy).
  2. Clarify and enforce `health_check.method` requirement semantics, and add/adjust tests accordingly.
  3. Align feature/task status metadata after reconciliation.

### Suggested Follow-up Improvements
- Add a normalization/alias strategy if both taxonomy sets are desired for compatibility (for example, allow both old/new tokens with a deprecation warning).
- Add a dedicated validator test for `health_check` object present without `method` to remove ambiguity.
- Add brief schema examples in docs once taxonomy is finalized to avoid future drift.


# Feature24 Review1 Reconciliation - SWE agent

## Summary
- Applied TechLead Review 1 fixes for feature24 taxonomy and health-check semantics.
- Updated schema constants to include canonical AC taxonomy (`mcp-server`, `vector-db`, `database`, `api`, `local-process`) and compatibility aliases (`postgres`, `redis`, `http-api`, `process`).
- Added alias mapping so legacy values are treated as canonical equivalents (including `process` == `local-process`).
- Enforced validator rule: if `health_check` object is declared, `health_check.method` is required.
- Updated feature24 AC wording in `FEATURES.txt` to explicitly describe canonical values, accepted aliases, and required method semantics.
- Expanded feature24 tests and inspect fixture types to reflect canonical taxonomy while preserving alias compatibility.

## Focused Test Results
- `python3 -m pytest tests/test_validator.py::test_feature24_services_optional_list_is_accepted tests/test_validator.py::test_feature24_service_required_fields_and_type_validation tests/test_validator.py::test_feature24_health_check_method_specific_validation tests/test_validator.py::test_feature24_no_services_regression_unchanged tests/test_validator.py::test_feature24_duplicate_service_names_rejected tests/test_cli_inspect.py::test_feature24_inspect_displays_services tests/test_regression_v1.py::test_feature24_ac_coverage_and_no_services_regression_gate` -> `7 passed`
- `python3 src/validate_project_manifests.py` -> `Validation passed: manifests are consistent`

## Teaching notes
- Canonical enums with compatibility aliases are a robust way to evolve schema contracts without forcing immediate breaking changes on users.
- In validation design, requiring a discriminator (`method`) whenever a nested config object exists removes ambiguity and makes downstream execution paths simpler.
- Feature-level AC text should be treated as part of the executable contract: when behavior evolves, update both tests/code and AC wording to keep governance artifacts trustworthy.

## Tech Lead Review 2

### Re-check Scope
- Verify Review1 items 1 and 2 are fully addressed after SWE reconciliation.
- Confirm support for `mcp-server` and `vector-db` service types.
- Clarify semantics difference between `process` and `local-process` service type values.

### Findings
- Review1 item 1 (service type taxonomy mismatch): addressed.
  - Canonical feature24 taxonomy is now supported in schema/validator, including `mcp-server` and `vector-db`.
  - Compatibility aliases are also supported to preserve backward compatibility (`postgres`, `redis`, `http-api`, `process`).
  - Feature AC text in `FEATURES.txt` now reflects canonical values plus accepted aliases.
- Review1 item 2 (missing `health_check.method` requirement): addressed.
  - Validator now enforces `health_check.method` whenever `health_check` is declared.
  - Missing-method behavior is explicitly covered by tests.
- Review1 item 3 (status alignment): addressed by user.
  - feature24 status is now `needs-review`.

### Clarification: `process` vs `local-process`
- `local-process` is the canonical feature24 service type.
- `process` is a backward-compatibility alias that maps to the same semantics as `local-process`.
- Practical meaning today: both indicate a service dependency represented by a process running on the local machine (used with `health_check.method: process` and `process_name` checks in future runtime integration).
- Guidance: use `local-process` in new manifests; keep `process` accepted for existing manifests during compatibility window.

### Evidence Checked
- Focused reconciliation test gate:
  - `python3 -m pytest tests/test_validator.py::test_feature24_services_optional_list_is_accepted tests/test_validator.py::test_feature24_service_required_fields_and_type_validation tests/test_validator.py::test_feature24_health_check_method_specific_validation tests/test_validator.py::test_feature24_no_services_regression_unchanged tests/test_validator.py::test_feature24_duplicate_service_names_rejected tests/test_cli_inspect.py::test_feature24_inspect_displays_services tests/test_regression_v1.py::test_feature24_ac_coverage_and_no_services_regression_gate`
  - Result: `7 passed`
- Full regression suite:
  - `python3 -m pytest`
  - Result: `222 passed, 1 skipped`

### Verdict
- Review1 items 1 and 2 are properly addressed.
- Feature24 is approved for merge from a Tech Lead review perspective.
