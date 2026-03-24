# Tests To Do Later

These test definitions were intentionally deferred to match implementation order:
1) feature23-feature26
2) feature27
3) feature19

## Deferred Test Definitions (moved from TESTS.txt)

```yaml
  - id: test214
    title: Feature19 import CLI validates required source and target args
    type: unit
    preconditions: kinnoo CLI installed
    steps:
      - step1: Run `kinnoo import` with missing arguments
      - step2: Verify usage/help guidance and non-zero exit
    expected: CLI validates required arguments and provides actionable usage text
    pass_criteria: non-zero exit and stderr includes import usage with required arguments
    automated: true
    automation_path: tests/test_cli.py::test_feature19_import_requires_source_and_target
    covers:
      - feature: feature19
        ac: AC1

  - id: test215
    title: Feature19 import blocks destructive overwrite without explicit confirmation
    type: unit
    preconditions: destination path already exists
    steps:
      - step1: Run `kinnoo import <source> <existing-destination>` without force/confirm
      - step2: Verify command aborts with clear collision error
    expected: Safety checks prevent accidental overwrites
    pass_criteria: non-zero exit with explicit collision guidance
    automated: true
    automation_path: tests/test_import.py::test_feature19_import_prevents_overwrite_without_explicit_confirmation
    covers:
      - feature: feature19
        ac: AC7

  - id: test216
    title: Feature19 import uses analyzer inference to generate manifest draft
    type: integration
    preconditions: analyzer returns inferred entrypoint/runtime/dependencies for fixture
    steps:
      - step1: Run import on fixture with recognizable project structure
      - step2: Inspect generated kinnoo.yaml values and import summary
    expected: Generated manifest is derived from analyzer report rather than static defaults only
    pass_criteria: inferred fields appear in output and match analyzer evidence
    automated: true
    automation_path: tests/test_import.py::test_feature19_import_uses_analyzer_inference_for_manifest
    covers:
      - feature: feature19
        ac: AC3

  - id: test217
    title: Feature19 import surfaces low-confidence analyzer warnings
    type: integration
    preconditions: fixture with ambiguous entrypoint/framework to trigger low-confidence outputs
    steps:
      - step1: Run import and capture summary output
      - step2: Verify warning/todo guidance appears for unresolved fields
    expected: Ambiguous inference is surfaced explicitly to users
    pass_criteria: warnings include unresolved field names and actionable next steps
    automated: true
    automation_path: tests/test_import.py::test_feature19_import_reports_low_confidence_fields
    covers:
      - feature: feature19
        ac: AC3
      - feature: feature19
        ac: AC9

  - id: test218
    title: Feature19 wizard confirms detected values before extra prompts
    type: integration
    preconditions: analyzer returns high-confidence values for most fields
    steps:
      - step1: Run import in interactive mode on high-confidence fixture
      - step2: Verify wizard shows detected values and asks confirmation
      - step3: Verify no extra prompts for fields already inferred confidently
    expected: Confirm-first UX minimizes unnecessary questions
    pass_criteria: prompt count is minimal and follows confirm-first ordering
    automated: true
    automation_path: tests/test_import.py::test_feature19_wizard_confirm_first_behavior
    covers:
      - feature: feature19
        ac: AC4

  - id: test219
    title: Feature19 wizard prompts only for missing or ambiguous fields
    type: integration
    preconditions: analyzer report includes intentionally missing/ambiguous fields
    steps:
      - step1: Run interactive import with mixed-confidence analyzer report
      - step2: Verify wizard prompts are limited to unresolved fields
    expected: Follow-up questions are conditional and targeted
    pass_criteria: prompted fields exactly match missing/ambiguous set
    automated: true
    automation_path: tests/test_import.py::test_feature19_wizard_prompts_only_for_unresolved_fields
    covers:
      - feature: feature19
        ac: AC4
      - feature: feature19
        ac: AC9

  - id: test220
    title: Feature19 import rollback cleans partial destination on failure
    type: integration
    preconditions: fixture that triggers failure after partial artifact creation
    steps:
      - step1: Run import and inject failure mid-flow
      - step2: Verify destination is removed or restored to clean pre-run state
    expected: Import does not leave broken partial output
    pass_criteria: destination path has no partial imported artifacts after failure
    automated: true
    automation_path: tests/test_import.py::test_feature19_import_rolls_back_partial_output_on_failure
    covers:
      - feature: feature19
        ac: AC5

  - id: test221
    title: Feature19 import handles Ctrl+C and EOF with safe cleanup
    type: integration
    preconditions: interactive import flow active
    steps:
      - step1: Trigger Ctrl+C or EOF during wizard confirmation
      - step2: Verify non-zero exit and cleanup of destination artifacts
    expected: Interrupts abort safely without leaving partial output
    pass_criteria: non-zero exit and no leftover partial artifacts in destination
    automated: true
    automation_path: tests/test_import.py::test_feature19_import_interrupt_cleanup
    covers:
      - feature: feature19
        ac: AC6

  - id: test222
    title: Feature19 imported agent can run through kinnoo run path
    type: integration
    preconditions: successful import fixture with resolved dependencies
    steps:
      - step1: Run import on existing agent fixture
      - step2: Execute `kinnoo run <imported-dir> "hello"`
      - step3: Verify non-empty stdout and successful execution
    expected: Imported scaffold is runnable through baseline run flow
    pass_criteria: run exits 0 and emits non-empty stdout
    automated: true
    automation_path: tests/test_import.py::test_feature19_imported_agent_runs_via_kinnoo_run
    covers:
      - feature: feature19
        ac: AC8

  - id: test223
    title: Feature19 import preserves source project files unchanged
    type: integration
    preconditions: source fixture with checksummed baseline file set
    steps:
      - step1: Capture source checksums before import
      - step2: Run import
      - step3: Compare source checksums after import
    expected: Import is non-destructive to source project
    pass_criteria: source file contents/checksums are unchanged
    automated: true
    automation_path: tests/test_import.py::test_feature19_import_does_not_mutate_source_project
    covers:
      - feature: feature19
        ac: AC2

  - id: test224
    title: Feature27 analyzer report schema is stable and deterministic
    type: unit
    preconditions: analyzer module available
    steps:
      - step1: Run analyzer on fixture project
      - step2: Validate report includes inferred fields, confidence, warnings, and evidence sections
      - step3: Re-run analyzer and compare ordering/structure
    expected: Analyzer report contract is stable for downstream consumers
    pass_criteria: report schema and key ordering remain deterministic across runs
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_analysis_report_schema_and_determinism
    covers:
      - feature: feature27
        ac: AC1
      - feature: feature27
        ac: AC7

  - id: test225
    title: Feature27 detects entrypoint runtime and framework with confidence
    type: unit
    preconditions: fixtures for one-shot and mcp/server-like project layouts
    steps:
      - step1: Run analyzer on known-layout fixtures
      - step2: Verify inferred entrypoint/runtime/framework values and confidence levels
    expected: Common layouts are detected accurately with confidence metadata
    pass_criteria: expected fields match fixtures and confidence exceeds configured threshold for known cases
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_detect_entrypoint_runtime_framework
    covers:
      - feature: feature27
        ac: AC2

  - id: test226
    title: Feature27 downgrades confidence for ambiguous runtime or framework signals
    type: unit
    preconditions: ambiguous fixture containing mixed/unclear runtime or framework patterns
    steps:
      - step1: Run analyzer on ambiguous fixture
      - step2: Verify low-confidence output and warning entries
    expected: Analyzer avoids overconfident false assertions on ambiguous inputs
    pass_criteria: confidence for ambiguous fields is below threshold and warnings are emitted
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_ambiguous_detection_lowers_confidence
    covers:
      - feature: feature27
        ac: AC2
      - feature: feature27
        ac: AC7

  - id: test227
    title: Feature27 dependency detection reads requirements and pyproject
    type: unit
    preconditions: fixtures with requirements.txt and pyproject dependency declarations
    steps:
      - step1: Run analyzer dependency detector on requirements fixture
      - step2: Run analyzer dependency detector on pyproject fixture
      - step3: Verify normalized dependency output
    expected: Detector reads both formats and emits normalized dependency list
    pass_criteria: output includes expected package specs with deterministic ordering
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_detect_dependencies_from_requirements_and_pyproject
    covers:
      - feature: feature27
        ac: AC3

  - id: test228
    title: Feature27 env-var detector extracts and deduplicates names
    type: unit
    preconditions: fixtures with multiple getenv/environ usage patterns
    steps:
      - step1: Run analyzer env-var detector
      - step2: Verify deduplicated env var list and stable ordering
    expected: Env var names are extracted reliably from source patterns
    pass_criteria: expected names present once each in deterministic order
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_detect_env_vars_deduplicated
    covers:
      - feature: feature27
        ac: AC4

  - id: test229
    title: Feature27 asset detector identifies model and data bundle candidates
    type: unit
    preconditions: fixture includes model/data artifact files and non-asset noise files
    steps:
      - step1: Run analyzer asset detector
      - step2: Verify expected candidate assets are included and unsafe/irrelevant paths are excluded
    expected: Asset detector proposes likely bundle paths with safety filtering
    pass_criteria: candidate set includes expected artifacts and excludes filtered paths
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_detect_assets_candidates
    covers:
      - feature: feature27
        ac: AC5

  - id: test230
    title: Feature27 service detector suggests typed service entries and health hints
    type: unit
    preconditions: fixture includes redis/postgres/http service usage patterns
    steps:
      - step1: Run analyzer service detector
      - step2: Verify suggested service entries include name/type and health check hints where inferable
    expected: Service suggestions map common patterns into manifest-compatible service objects
    pass_criteria: detected services include expected types and method-specific health check hints
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_detect_services_with_health_hints
    covers:
      - feature: feature27
        ac: AC6

  - id: test231
    title: Feature27 merge helper applies user overrides above inferred values
    type: unit
    preconditions: analyzer output and explicit override inputs available
    steps:
      - step1: Merge analyzer inferred manifest with user overrides
      - step2: Verify override precedence and unchanged inferred values for untouched fields
    expected: Merge behavior is deterministic and respects explicit user intent
    pass_criteria: override fields win and non-overridden fields remain inferred values
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_merge_user_overrides_precedence
    covers:
      - feature: feature27
        ac: AC7
      - feature: feature27
        ac: AC8

  - id: test232
    title: Feature27 confidence threshold emits unresolved-field warnings
    type: unit
    preconditions: analyzer confidence threshold and ambiguous fixture configured
    steps:
      - step1: Run analyzer with threshold enabled on ambiguous fixture
      - step2: Verify unresolved fields are flagged with warning/todo guidance
    expected: Low-confidence fields are explicitly surfaced for follow-up
    pass_criteria: warning list includes unresolved fields and actionable guidance text
    automated: true
    automation_path: tests/test_analyzer.py::test_feature27_confidence_threshold_warnings
    covers:
      - feature: feature27
        ac: AC7
      - feature: feature27
        ac: AC9
```