# Task494 Post-Implementation Notes

- Extended dependency inference to parse Poetry dependencies from `tool.poetry.dependencies`.
- Added package.json dependency extraction into analyzer dependency inference.
- Extended env-var inference to include Node.js `process.env` patterns.
- Added regression tests `test703` and `test704`.

## Teaching Notes

- Cross-ecosystem analyzers should aggregate multiple metadata sources (requirements, pyproject, package.json).
- Keep normalization logic centralized so dependency output stays stable and deterministic.
- Generic-agent inference benefits from language-specific env-var pattern extraction.
