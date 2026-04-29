# task348 notes

## Summary
- Added new declarative tests module at src/kinnoo/test_command.py with standardized kinnoo.tests.yaml schema parsing and deterministic validation diagnostics.
- Added schema support for test declarations in manifests: tests_file, tests_version, and inline tests optional fields.
- Added validator hook to validate inline test declarations embedded in kinnoo.yaml.
- Added CLI surface for kinnoo test with validate-only flow and optional JSON output, enabling parser-first contract validation.
- Added regression test test_feature69_standardized_tests_file_parser covering canonical file parsing, invalid fixture diagnostics, and inline fallback loading.
- Updated schema reference docs with canonical kinnoo.tests.yaml format, compatibility bridge behavior, and anti-pattern guidance.

## Teaching Notes
- Declarative test specs are strongest when validation errors are path-specific and deterministic (for example, tests[0].assertions) so CI fixes are fast.
- A compatibility bridge (canonical file plus inline/linked fallback) reduces migration friction while preserving one stable preferred format.
- Parse-time validation and run-time execution should stay separated: parser errors should fail before any runtime process starts.
- Assertion DSL scope should be narrow early (contains/equals/regex) to avoid brittle, over-flexible contracts in v1.

## Validation
- python3 -m pytest tests --testmon -k test_feature69_standardized_tests_file_parser
