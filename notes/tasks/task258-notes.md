# Task258 Notes - Analyzer Input/Output Type Auto-Detection

Date: 2026-03-22

## Scope Implemented

Implemented task258 by extending analyzer inference to detect input and output contract types, wiring those detections into import-generated manifests, and adding targeted automated tests mapped to test364/test365.

## What Changed

### 1) Analyzer detectors
Updated `src/kinnoo/analyzer.py`:
- Added `_detect_input_type(project_dir)`:
  - Detects JSON input when `json.loads(...)` is used with CLI argument handling (`sys.argv` or `parse_args`).
  - Detects parameterized CLI patterns (argparse `add_argument` + `parse_args`) and maps them to `inputs: json` because structured payloads are the safest manifest-compatible representation.
  - Detects text input from `sys.argv[...]` and `input()` usage.
  - Falls back to `inputs: text` with low confidence + warning if no clear signal exists.
- Added `_detect_output_type(project_dir)`:
  - Detects JSON output via `json.dumps(...)`.
  - Detects structured return literals as JSON-leaning when no print-based text output is present.
  - Detects text output via `print(...)` usage.
  - Falls back to `outputs: text` with low confidence + warning if no clear signal exists.
- Wired both detectors into `_detector_registry()` under keys `inputs` and `outputs` so they are included in `AnalysisReport.inferred` and `AnalysisReport.confidence`.

### 2) Import wizard integration
Updated `src/kinnoo/import_command.py`:
- `_show_detected_values(...)` now displays analyzer-detected `inputs` and `outputs` alongside existing fields.
- `_build_manifest_from_analysis(...)` now writes detected types into generated `kinnoo.yaml`:
  - `inputs.type` uses inferred value when valid.
  - `outputs.type` uses inferred value when valid.
  - Values are guarded to supported manifest types (`text`, `string`, `file`, `json`) and fall back to `string` if out of contract.

## Tests Added (Task258)

Updated `tests/test_validator.py`:
- `test_analyzer_detects_text_input_type` (test364)
  - Fixture uses `sys.argv[1]`.
  - Asserts `inferred.inputs == "text"`, confidence `>= 0.7`, and evidence includes `sys.argv`.
- `test_analyzer_detects_json_input_type` (test365)
  - Fixture uses `json.loads(sys.argv[1])`.
  - Asserts `inferred.inputs == "json"`, confidence `>= 0.7`, and evidence includes `json.loads`.

## Targeted Test Runs

Command:
```bash
python3 -m pytest tests/test_validator.py -k "test_analyzer_detects_text_input_type or test_analyzer_detects_json_input_type" -q
```
Result:
```text
2 passed, 42 deselected
```

Command:
```bash
python3 -m pytest tests/test_cli_import.py -k "confirm_first_wizard_prompt_minimization or keeps_inferred_entrypoint_without_reprompt" -q
```
Result:
```text
2 passed, 16 deselected
```

## Teaching Notes

### Why this detector design is intentionally heuristic
Static AST analysis is fast and safe (no code execution), but it cannot fully prove runtime behavior. For agent onboarding, this is usually the right tradeoff:
- High precision for common patterns (`sys.argv`, `json.loads`, `print`, `json.dumps`).
- Conservative fallback with confidence + warnings when evidence is weak.
- Human-in-the-loop verification still possible in import flow.

### Practical ML/agentic analogy
This analyzer behaves like a lightweight rule-based classifier with calibrated confidence metadata:
- Features: AST patterns (calls, subscripts, imports).
- Class labels: `text` or `json` (manifest-compatible IO contract types).
- Confidence: handcrafted priors based on signal strength.
- Explainability: evidence strings provide traceable rationale.

This mirrors production agent-evaluation principles: deterministic extraction + explicit uncertainty reporting + operator override.

### Extension path for future task iterations
If we later need richer contracts (`none`, `parameterized`, full schema), we should evolve to:
1. Introduce explicit manifest fields for structured input schema (for example `inputs.parameters`).
2. Keep `inputs.type` as coarse transport contract (`text/json/file`).
3. Add detector outputs for parameter names/types from argparse signatures.
4. Expand regression tests to include mixed patterns and ambiguous confidence thresholds.
