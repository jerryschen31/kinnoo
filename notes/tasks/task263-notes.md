# Task263 Notes - Add --language Flag to kinnoo init

Date: 2026-03-22

## Scope Implemented

Implemented `kinnoo init --language` with python/js/ts support, framework-language compatibility checks, and language-only barebones scaffolds.

## What Changed

- Updated src/kinnoo/cli.py:
  - Added `--language` choices to `init` parser: `python`, `js/javascript`, `ts/typescript`.
  - Passed language through to `init_agent(...)`.
- Updated src/kinnoo/init_command.py:
  - Added supported language aliases and framework compatibility matrix.
  - Enforced deterministic incompatibility error for invalid framework-language combinations.
  - Added language-only JS and TS scaffolds (run.js/run.ts, package.json, README, and nodejs runtime manifest fields).
  - Preserved existing behavior when language is omitted.

## Tests Added

- tests/test_cli.py::test_init_language_python (test372)
- tests/test_cli.py::test_init_incompatible_framework_language (test373)

## Targeted Test Run

```bash
python3 -m pytest tests/test_cli.py -k "test_init_language_python or test_init_incompatible_framework_language" -q
```

Result:

```text
2 passed
```

## Teaching Notes

This change introduces a compatibility matrix pattern:
- Inputs: framework, language.
- Rule engine: allowed language set per framework.
- Output: scaffold plan or deterministic error.

This is the same architecture often used in AI orchestration systems for tool-policy enforcement (policy table + canonicalized inputs + explicit failure mode).