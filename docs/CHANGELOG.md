# Changelog

All notable changes to this project will be documented in this file.


## [v0.11.0] - 2026-03-16
### Added
- Implemented Feature24 "Service Declarations - Manifest Schema" with optional `services` manifest support.
- Added canonical service type taxonomy support: `mcp-server`, `vector-db`, `database`, `api`, `local-process`.
- Added backward-compatible service type aliases: `postgres`, `redis`, `http-api`, `process`.
- Added inspect output support for declared services, including service names, types, and health-check configuration fields.

### Changed
- Extended validator checks for `services` objects:
  - required fields (`name`, `type`)
  - allowed-value validation for service types and health-check methods
  - method-specific health-check field requirements (`port`, `url`, `process_name`)
  - duplicate service-name rejection
- Enforced that `health_check.method` is required whenever `health_check` is declared.
- Updated feature24 acceptance criteria text to align canonical values and compatibility alias policy.

### Quality
- Feature24 focused AC/reconciliation suite passed: `7 passed`.
- Full regression suite passed after feature24 updates: `222 passed, 1 skipped`.


## [v0.10.0] - 2026-03-16
### Added
- Implemented Feature23 "MCP Server Runtime Type - Schema & Lifecycle".
- Added `mcp-server` as a supported `runtime.type` value alongside `one-shot`.
- Added dedicated supervisor lifecycle support for MCP server execution in `kinnoo run`, including readiness gating and long-running process management.
- Added readiness strategies for explicit `runtime.readiness_probe` modes (`tcp`, `stdout`) with fallback to `runtime.port` TCP probing or immediate-ready when no probe config is provided.

### Changed
- Extended `kinnoo run` runtime branching to treat `mcp-server` agents as long-running services rather than one-shot executions.
- Added graceful Ctrl+C handling for MCP server mode: SIGTERM-first shutdown with timeout-based SIGKILL escalation for unresponsive processes.
- Extended run trace logging for MCP server sessions to include lifecycle metadata (`start_timestamp`, `stop_timestamp`, `server_exit_code`, `server_exit_signal`, `shutdown_sigterm_sent`, `shutdown_sigkill_sent`).

### Quality
- Added and validated feature23 coverage tests (`test214` through `test221`) across validator support, readiness behavior, streaming, shutdown semantics, trace metadata, fallback behavior, and one-shot regression protection.
- Executed full regression suite after feature23 integration: `215 passed, 1 skipped`.


## [v0.9.0] - 2026-03-16
### Added
- Implemented Feature22 "Asset Bundling" with manifest-level `assets` support (`paths`, `bundle`, `max_bundle_size_mb`).
- Added recursive asset inclusion during `kinnoo pack` for declared files/directories when bundling is enabled.
- Added install-time extraction support so bundled assets are restored to their original relative paths.
- Added inspect visibility for declared asset paths and asset size details.

### Security
- Added path-traversal protection for declared asset paths during packing.
- Added non-blocking asset credential risk sweep with filename-pattern warnings and size-limited UTF-8 text pattern scanning.
- Expanded filename warning coverage to align with feature22 examples, including `.key`, `*.p12`, and `*.pfx`.

### Changed
- `kinnoo pack` now honors `assets.bundle: false` as an explicit opt-out while keeping manifest declarations intact.
- Archive large-size warnings now support per-agent override via `assets.max_bundle_size_mb`.

### Quality
- Feature22-focused validation and regression suites passed across validator, pack, install extract, inspect, and regression gate coverage.


## [v0.8.0] - 2026-03-15
### Added
- Implemented Feature20 "Flexible Runtime Inputs" for `kinnoo run`.
- Added support for no-input execution when manifests declare `inputs.required: false`.
- Added pass-through invocation mode via `--` with verbatim argv forwarding to the agent entrypoint.
- Added explicit protection so required input cannot be bypassed by pass-through arguments.

### Changed
- Updated run CLI usage/help messaging to document all three supported invocation modes (single input, no-input, pass-through).
- Extended feature20 test coverage with focused assertions for required-input enforcement and usage guidance output.

### Quality
- Feature20 follow-up regression checks passed, including required-input/pass-through compatibility paths.


## [v0.7.0] - 2026-03-13
### Added
- Completed Phase 2 feature delivery and validation across runtime safety, trust, archive integrity, and packaging UX.
- Finalized input safety guard coverage in `kinnoo run`, including type-aware detection, interactive warn-and-confirm flow, and CI-friendly bypass controls.
- Finalized archive size reporting and visibility across `kinnoo pack`, `kinnoo inspect`, and `kinnoo list`.

### Changed
- Consolidated and stabilized registry/archive publish-install flows introduced in Phase 2, including local archive-first packaging and remote-mode abstractions.
- Improved install and pack test stability for non-interactive trust confirmation and archive destination handling.

### Quality
- Phase 2 closeout validation completed:
  - Manifest validation: `python3 src/validate_project_manifests.py` passed
  - Full test suite: `158 passed, 1 skipped`


## [v0.6.0] - 2026-03-13
### Added
- Implemented Feature18 "Input Safety Guard" with pre-entrypoint input threat detection in `kinnoo run`.
- Added pluggable guard architecture via `InputGuard` protocol and `get_default_guard()` factory for future ML-based guard replacement.
- Added V1 `RegexInputGuard` coverage for SQL injection, shell command injection, path traversal, SSRF, XSS, and template injection patterns.
- Added type-aware guard checks for input types (`text`, `string`, `file_path`, `url`, `id`) and aggregated multi-parameter checking via `check_inputs()`.
- Added `--no-guard` override for trusted CI/automation workflows.

### Changed
- `kinnoo run` now warns on flagged input and prompts `Proceed anyway? [y/N]` in interactive mode.
- Non-interactive execution now fails closed on flagged input unless `--no-guard` is provided.
- Added focused regression coverage in `tests/test_input_guard.py`, `tests/test_input_guard_integration.py`, and docs contract coverage in `tests/test_docs.py` for feature18 behavior.

### Quality
- TechLead pre-merge validation passed:
  - Feature18-focused suite: `16 passed`
  - Full repository suite: `156 passed, 1 skipped`


## [v0.5.0] - 2026-03-12
### Added
- Implemented Feature17 "Pack Size Reporting & Warnings" across pack/inspect/list workflows.
- Added pack-time archive size output: `[kinnoo pack] Archive size: <human-readable>`.
- Added large-archive warning for artifacts exceeding 100 MB: `Warning: archive is large (X MB). Consider whether all dependencies are necessary.`
- Added archive size visibility in `kinnoo inspect <archive.kno>` and list outputs (`kinnoo list`, `kinnoo list --local`, `kinnoo list --remote`).
- Added focused regression coverage in `tests/test_pack_size_reporting.py` and docs contract coverage in `tests/test_docs.py` for feature17 behavior.

### Changed
- Stabilized install tests to explicitly handle trust-confirmation behavior in non-interactive flows (`--yes` where prompt behavior is not under test).
- Stabilized pack tests around canonical archive backend destination semantics using isolated `KINNOO_ARCHIVE_ROOT` test paths.

### Quality
- Full repository validation now passes after stabilization: `140 passed, 1 skipped`.


## [v0.4.0] - 2026-03-11
### Added
- Implemented Feature16 "Archive Integrity (Checksums)" across pack/install/inspect/publish workflows.
- Added checksum sidecar generation during pack using sibling `.kno.sha256` files with stable `<sha256>  <archive-filename>` format.
- Added install-time checksum verification for file-path installs when sidecar exists, with explicit archive integrity failure behavior on mismatch.
- Added install warning-only fallback when checksum sidecar is missing: `No checksum file found — archive integrity not verified`.
- Added archive checksum visibility in `kinnoo inspect` and checksum sidecar propagation in `kinnoo publish` when source sidecar is present.

### Security
- Strengthened artifact provenance and tamper detection by validating archive digests before extraction side effects.


## [v0.3.0] - 2026-03-11
### Added
- Implemented Feature15 "Trust Baseline" across install, run, inspect, and pack flows.
- Added install-time trust summary with confirmation prompt and `--yes`/`-y` automation bypass.
- Added unverified-source warning path when installing raw `.kno` archives without sidecar checksum files.
- Added UTC JSON run trace logging at `~/.kinnoo/logs/run.<TIMESTAMP>.log` with safe fields only (`timestamp`, `agent_name`, `agent-version`, `runtime_type`, `exit_code`).
- Added heuristic env-var exposure sweep integrated into `kinnoo inspect` and non-blocking warnings in `kinnoo pack`.

### Security
- Reinforced the project-wide invariant that secret/env var values are never emitted in trust-related output or logs; only names may be shown.


## [v0.2.0] - 2026-03-05
### Changed
- Refactored `pack` and `publish` flows in Feature13 to use the registry abstraction and source-mode path consistently.
- Improved packaging/publishing reliability through shared backend handling and updated test coverage.

### Deprecated
- Feature12 legacy registry path/tests were deprecated and documented to prevent accidental re-enable.


## [v0.1.1] - 2026-03-05
### Added
- Implemented `kinnoo pack` command for packaging projects.
- Enhanced `kinnoo install` with improved functionality and support for packaged projects.

## [v0.1.0] - 2026-02-25
### Added
- Initial release.
- Implemented all MVP features:
  - `kinnoo init` for project initialization.
  - `kinnoo run` for running projects.
  - `kinnoo install` for installing dependencies.
