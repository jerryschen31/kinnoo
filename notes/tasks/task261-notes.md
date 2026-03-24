# Task261 Notes - Analyzer Model Auto-Detection

Date: 2026-03-22

## Scope Implemented

Implemented model auto-detection in the analyzer and wired it into import-generated manifests.

## What Changed

- Updated src/kinnoo/analyzer.py:
  - Added `_detect_model(project_dir)` detector.
  - Detects explicit keyword model literals (`model=`, `model_name=`, `model_id=`) with high confidence.
  - Detects model-like assignment literals (`MODEL_NAME = "..."`) with medium confidence.
  - Falls back to heuristic model-like string literal detection with warning.
  - Added `model` to `_detector_registry()` so it appears in `AnalysisReport`.
- Updated src/kinnoo/import_command.py:
  - Detected values display now includes `model`.
  - Generated manifest includes `model: <value>` when inference returns a non-empty string.

## Tests Added

- tests/test_validator.py::test_analyzer_detects_model_gemini (test369)
- tests/test_validator.py::test_analyzer_detects_model_chatgpt (test370)

## Targeted Test Run

```bash
python3 -m pytest tests/test_validator.py -k "test_analyzer_detects_model_gemini or test_analyzer_detects_model_chatgpt" -q
```

Result:

```text
2 passed, 44 deselected
```

## Teaching Notes

Model inference here is a static-program-analysis classifier:
- Features: AST call keywords, assignments, and string literals.
- Output: one best candidate model identifier plus confidence/evidence.
- Safety: no code execution, no network calls.

For interview framing: this is a deterministic "weak supervision" approach. It is explainable and cheap, and it works well as an onboarding prior before human confirmation.