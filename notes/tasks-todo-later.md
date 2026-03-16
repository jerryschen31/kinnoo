# Tasks To Do Later

These task definitions were intentionally deferred to match implementation order:
1) feature23-feature26
2) feature27
3) feature19

## Deferred Task Definitions (moved from TASKS.txt)

```yaml
  - id: task141
    title: "Feature19 import CLI and safety envelope"
    type: task
    description: |
      Implement `kinnoo import` command wiring and argument validation for
      source/target paths, non-destructive behavior, and overwrite safety gates.
    files:
      - src/kinnoo/cli.py
      - src/kinnoo/import_command.py
      - tests/test_cli.py
      - tests/test_import.py
    steps:
      - 'step1: Add `import` subcommand parsing with required source and destination arguments'
      - 'step2: Validate source exists and destination does not exist unless explicit overwrite path is confirmed'
      - 'step3: Keep error messages actionable for missing args, invalid paths, and collision scenarios'
      - 'step4: Add CLI-focused tests for usage/help and non-destructive safety checks'
    dependencies: [task10]
    tests: [test214, test215]
    status: not-started

  - id: task142
    title: "Feature19 integrate analyzer into import flow"
    type: task
    description: |
      Integrate feature27 analyzer output into `kinnoo import` so inferred fields,
      confidence, and warnings drive manifest draft generation.
    files:
      - src/kinnoo/import_command.py
      - src/kinnoo/analyzer.py
      - tests/test_import.py
    steps:
      - 'step1: Call `analyze_project()` during import and capture structured report output'
      - 'step2: Map inferred values into a manifest draft with deterministic field ordering'
      - 'step3: Surface analyzer warnings/todos in import summary output'
      - 'step4: Add tests for high-confidence and low-confidence inference handling'
    dependencies: [task141, task146]
    tests: [test216, test217]
    status: not-started

  - id: task143
    title: "Feature19 confirm-first interactive wizard"
    type: task
    description: |
      Build an interactive wizard that confirms detected analyzer values first and
      asks additional questions only for missing or ambiguous fields.
    files:
      - src/kinnoo/import_command.py
      - tests/test_import.py
    steps:
      - 'step1: Present grouped detected fields (runtime, deps, env, assets, services) for user confirmation'
      - 'step2: Prompt only for unresolved/ambiguous fields based on analyzer confidence thresholds'
      - 'step3: Support non-interactive mode with fail-safe abort for unresolved required fields'
      - 'step4: Add tests for confirm-all, selective override, and missing-field prompt behavior'
    dependencies: [task142]
    tests: [test218, test219]
    status: not-started

  - id: task144
    title: "Feature19 artifact copy and rollback guarantees"
    type: task
    description: |
      Ensure import creates complete scaffold output and performs robust cleanup on
      errors or user interruption, leaving no broken partial destination.
    files:
      - src/kinnoo/import_command.py
      - tests/test_import.py
    steps:
      - 'step1: Copy required artifacts (`entrypoint`, requirements, README, tools/prompts when present) without mutating source project'
      - 'step2: Implement transactional destination creation with rollback on exceptions'
      - 'step3: Handle Ctrl+C/EOF during wizard flow with safe abort and cleanup'
      - 'step4: Add tests for rollback and interrupt safety behavior'
    dependencies: [task143]
    tests: [test220, test221]
    status: not-started

  - id: task145
    title: "Feature19 import run/pack readiness validation"
    type: task
    description: |
      Validate that imported agents are immediately usable in baseline run/pack
      workflows with clear next-step guidance when dependencies are unresolved.
    files:
      - src/kinnoo/import_command.py
      - tests/test_import.py
      - tests/test_cli.py
    steps:
      - 'step1: Add post-import summary with commands for validate/run/pack checks'
      - 'step2: Add smoke test proving imported fixture runs via `kinnoo run` after standard dependency setup'
      - 'step3: Add regression check that import warnings remain non-silent and actionable'
      - 'step4: Capture review evidence for AC8 runnability contract'
    dependencies: [task144]
    tests: [test222, test223]
    status: not-started

  - id: task146
    title: "Feature27 analyzer module foundation and report contract"
    type: task
    description: |
      Create the analyzer module and a stable report schema consumed by import and
      other onboarding flows.
    files:
      - src/kinnoo/analyzer.py
      - tests/test_analyzer.py
    steps:
      - 'step1: Define `AnalysisReport` structure with inferred values, confidence, warnings, and detector evidence'
      - 'step2: Implement `analyze_project(project_dir)` orchestration over detector functions'
      - 'step3: Keep detector execution deterministic and non-fatal on individual detector errors'
      - 'step4: Add tests for report schema shape and deterministic ordering expectations'
    dependencies: [task50]
    tests: [test224]
    status: not-started

  - id: task147
    title: "Feature27 detect entrypoint runtime and framework"
    type: task
    description: |
      Implement detector logic for entrypoint, runtime, and framework inference
      across common one-shot and server-like Python agent layouts.
    files:
      - src/kinnoo/analyzer.py
      - tests/test_analyzer.py
    steps:
      - 'step1: Detect candidate entrypoints from common filenames and `__main__` guards'
      - 'step2: Infer runtime language/version/type and port hints using project metadata and code patterns'
      - 'step3: Infer framework using import signature matching (langchain, pydantic-ai, langgraph, openai-agents, mcp-related)'
      - 'step4: Add tests for confident detection and ambiguity downgrade paths'
    dependencies: [task146]
    tests: [test225, test226]
    status: not-started

  - id: task148
    title: "Feature27 detect dependencies and env vars"
    type: task
    description: |
      Implement dependency and environment-variable detectors for requirements,
      pyproject metadata, and source-code env access patterns.
    files:
      - src/kinnoo/analyzer.py
      - tests/test_analyzer.py
    steps:
      - 'step1: Parse dependencies from requirements.txt and pyproject project dependency lists'
      - 'step2: Normalize dependency entries into deterministic list format suitable for manifest generation'
      - 'step3: Detect env vars from `os.getenv`, `os.environ[]`, and equivalent patterns with deduplication'
      - 'step4: Add tests for parser edge cases and env var extraction coverage'
    dependencies: [task146]
    tests: [test227, test228]
    status: not-started

  - id: task149
    title: "Feature27 detect assets and external services"
    type: task
    description: |
      Implement detectors for likely asset bundle candidates and service declaration
      suggestions (service type plus health-check hints when available).
    files:
      - src/kinnoo/analyzer.py
      - tests/test_analyzer.py
    steps:
      - 'step1: Detect likely assets from model/data extensions and project directories with path-safety checks'
      - 'step2: Detect service hints from connection strings/import usage (redis/postgres/http/local process patterns)'
      - 'step3: Generate suggested service objects compatible with manifest schema expectations'
      - 'step4: Add tests for positive detection and false-positive suppression heuristics'
    dependencies: [task146]
    tests: [test229, test230]
    status: not-started

  - id: task150
    title: "Feature27 confidence scoring and manifest merge helpers"
    type: task
    description: |
      Add confidence scoring thresholds, unresolved-field warnings, and helper
      utilities for merging inferred values into manifest drafts used by import.
    files:
      - src/kinnoo/analyzer.py
      - src/kinnoo/import_command.py
      - tests/test_analyzer.py
      - tests/test_import.py
    steps:
      - 'step1: Implement per-field confidence levels and reason/evidence metadata'
      - 'step2: Emit warning/todo entries for unresolved or low-confidence fields'
      - 'step3: Provide helper for merging analyzer output with explicit user overrides'
      - 'step4: Add tests for merge precedence, warning emission, and confidence threshold behavior'
    dependencies: [task147, task148, task149]
    tests: [test231, test232]
    status: not-started
```