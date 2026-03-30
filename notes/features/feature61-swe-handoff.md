# Feature61 SWE Handoff

## Scope
- Feature: feature61
- Tasks: task332, task333
- Tests: test491, test492
- Dependencies: none

## Goal
Implement first-class registry auth UX in CLI with `kinnoo login` and `kinnoo logout`, supporting both interactive operators and automation.

## Task Guidance

### task332
Key outcomes:
- Add `login` and `logout` subcommands in CLI.
- Support interactive credential prompts and flag-driven non-interactive login.
- Persist token + tenant_slug + registry in local config.
- Ensure publish and registry client code can consume persisted auth.

### task333
Key outcomes:
- Add integration tests for interactive and non-interactive login.
- Add logout tests proving state cleanup and expected unauthorized behavior post-logout.
- Update README docs for auth command usage and auth-state precedence.

## AC to Test Mapping
- AC1 -> test491
- AC2 -> test491
- AC3 -> test492
- AC4 -> test492

## Constraints
- Never print secrets/tokens in output or logs.
- Keep env var override behavior backward-compatible.
