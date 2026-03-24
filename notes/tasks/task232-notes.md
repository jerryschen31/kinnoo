# Task232 - feature28 CLI command integration with backend abstraction

## Summary
- Updated CLI wiring in src/kinnoo/cli.py for backend mode selection across registry-facing commands.
- Added install flags: `--local` and `--remote` (mutually exclusive) for explicit registry source selection.
- Added publish flag: `--remote` and validation preventing `--local` + `--remote` together.
- Updated list/search dispatch defaults to `auto` mode:
  - explicit `--local` => local
  - explicit `--remote` => remote
  - no flag => remote when registry URL is configured, otherwise local
- Updated publish command in src/kinnoo/publish_command.py:
  - backend selection now supports local/remote/auto
  - remote backend uses RemoteRegistryClient with config/env values
  - clear config error if remote mode is selected but URL/token/tenant is incomplete
- Updated install command in src/kinnoo/install_command.py:
  - backend selection supports local/remote/auto for registry selectors
  - `--local` forces local backend even when remote config exists
  - `--remote` forces remote backend
  - remote resolve path now downloads archive from returned `download_url` and then reuses existing archive install flow
- Updated list/search command modules to support config-backed remote selection while preserving legacy mock-remote behavior when no remote URL is configured.
- Added mapped regression test330 in tests/test_cli.py as test_backend_selection.

## Tests and results
- `python3 -m pytest tests/test_cli.py::test_backend_selection` -> `1 passed`

## Bug/error notes
- Bug class: test double constructor mismatch in `test_backend_selection` (`_FakeLocalBackend` init signature).
- Attempts for this bug class: `1` (cap: `5`).
- Resolution: updated fake backend to accept `*args, **kwargs` to match production constructor usage.

## Teaching notes
- Backend selection logic should be centralized as a deterministic precedence matrix (explicit flags first, then config defaults). This avoids inconsistent behavior across commands.
- “Auto mode” is useful only when paired with clear fallback semantics; here it means remote-if-configured else local, which preserves existing local workflows for users without remote config.
- Reusing the existing install pipeline after remote download reduces risk: once a `.kno` is staged locally, validation/extraction/security checks remain identical and battle-tested.
- In tests for selection/routing behavior, prefer fakes around boundaries (backend constructors and resolver calls) so assertions focus on decision logic instead of network/filesystem side effects.
