# Feature 97 — SWE Handoff: Public GitHub Repository Preparation

## Context
Audit and prepare the repository for public visibility.

## Files to Create
- `CONTRIBUTING.md` — Dev setup, testing, PR guidelines
- `CODE_OF_CONDUCT.md` — Standard Contributor Covenant
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `.github/PULL_REQUEST_TEMPLATE.md`

## Files to Modify
- `.gitignore` — Ensure coverage of: `__pycache__/`, `*.egg-info/`, `*.kno`, `env/`, `scratch/`, `outputs/`, `notes/`, `.env`, `*.pyc`, `dist/`, `build/`

## Tasks
1. **Secret audit** — Search all tracked files for API keys, passwords, tokens. Use `grep -rn` for common patterns (password, secret, api_key, token, etc.)
2. **Internal content audit** — Identify files that should be gitignored for public release (notes/, scratch/, outputs/)
3. **Create community files** — CONTRIBUTING.md, CODE_OF_CONDUCT.md, issue/PR templates
4. **Verify LICENSE** — Confirm MIT license text is correct
5. **.gitignore update** — Add missing patterns

## Implementation Notes
- CONTRIBUTING.md should include: how to set up dev environment, how to run tests, coding standards, PR process
- Use Contributor Covenant v2.1 for CODE_OF_CONDUCT.md
- Issue templates should use GitHub's YAML format if possible
- notes/ and scratch/ contain internal planning — gitignore for public release

## Dependencies
- None

## Acceptance Criteria Summary
1. No secrets in tracked files
2. Community files created
3. .gitignore covers all generated/internal files
