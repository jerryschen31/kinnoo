# Task188 - feature33 manifest docs updates for OpenClaw and generic Node examples

## Summary
- Updated [docs/manifest-schema-reference.md](docs/manifest-schema-reference.md) with feature33 documentation:
  - documented `runtime.package_manager`, `channels`, `skills`, and `state_dirs` with type/path constraints,
  - documented OpenClaw-targeted validation expectations for `framework: openclaw`,
  - documented non-openclaw optional/non-breaking behavior.
- Added concrete manifest examples in schema docs:
  - OpenClaw Node.js daemon example (`framework: openclaw`, `runtime.type: daemon`, `runtime.package_manager`, `channels` including `stdio`),
  - Generic Node.js example using optional feature33 fields in non-openclaw mode.
- Updated [README.md](README.md) with concise feature33 guidance:
  - field constraints,
  - openclaw-targeted requirements,
  - non-openclaw compatibility behavior.
- Added task-linked docs regression test in [tests/test_docs.py](tests/test_docs.py):
  - `test_feature33_manifest_extension_docs_examples` (test286),
  - asserts presence of required field guidance and both required example categories.
- Updated [TASKS.txt](TASKS.txt):
  - `task188` moved to `needs-review`.

## Tests and results
- `python3 -m pytest tests/test_docs.py::test_feature33_manifest_extension_docs_examples` -> `1 passed`

## Bug/error notes
- No bugs encountered.
- Same bug/error class fix attempts: `0`.

## Teaching notes
- Documentation tasks should be validated with executable assertions (docs tests), not just manual review; this prevents future drift when content is refactored.
- For schema contract docs, include both constraints and examples: constraints define validity, examples demonstrate operator intent.
- Add explicit compatibility notes whenever introducing framework-targeted behavior so users can reason about additive vs. breaking changes quickly.
