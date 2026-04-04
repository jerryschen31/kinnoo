# task351 notes

## Summary
- Added release-note updates in docs/CHANGELOG.md for Feature69 and Feature70 documentation delivery.
- Added Phase 6 documentation sync checklist in notes/phases/phase6-planning-6.md for strict mode, lockfile, diff, uninstall, and import adapter command snippets.
- Added README consistency references for strict trust mode, frozen lockfile mode, diff, uninstall, and framework import adapters.
- Added regression test test_feature70_provenance_docs_and_regression in tests/test_docs.py to enforce provenance and command-reference consistency across README/schema/planning docs.

## Teaching Notes
- Documentation drift is easiest to prevent when the same command snippets are asserted across multiple source-of-truth files.
- Release notes should capture docs-contract changes, not only code behavior changes, because docs are part of the operator interface.
- Consistency tests should avoid overfitting to exact phrasing; verify semantic anchors (command shapes and provenance nouns) instead.
- Planning docs can serve as test fixtures when they include explicit command forms that downstream docs must mirror.

## Validation
- python3 -m pytest tests --testmon -k test_feature70_provenance_docs_and_regression
