# Changelog

All notable changes to this project will be documented in this file.


## [v2.0.0] - 2026-03-13
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


## [v1.6.0] - 2026-03-13
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


## [v1.5.0] - 2026-03-12
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


## [v1.4.0] - 2026-03-11
### Added
- Implemented Feature16 "Archive Integrity (Checksums)" across pack/install/inspect/publish workflows.
- Added checksum sidecar generation during pack using sibling `.kno.sha256` files with stable `<sha256>  <archive-filename>` format.
- Added install-time checksum verification for file-path installs when sidecar exists, with explicit archive integrity failure behavior on mismatch.
- Added install warning-only fallback when checksum sidecar is missing: `No checksum file found — archive integrity not verified`.
- Added archive checksum visibility in `kinnoo inspect` and checksum sidecar propagation in `kinnoo publish` when source sidecar is present.

### Security
- Strengthened artifact provenance and tamper detection by validating archive digests before extraction side effects.


## [v1.3.0] - 2026-03-11
### Added
- Implemented Feature15 "Trust Baseline" across install, run, inspect, and pack flows.
- Added install-time trust summary with confirmation prompt and `--yes`/`-y` automation bypass.
- Added unverified-source warning path when installing raw `.kno` archives without sidecar checksum files.
- Added UTC JSON run trace logging at `~/.kinnoo/logs/run.<TIMESTAMP>.log` with safe fields only (`timestamp`, `agent_name`, `agent-version`, `runtime_type`, `exit_code`).
- Added heuristic env-var exposure sweep integrated into `kinnoo inspect` and non-blocking warnings in `kinnoo pack`.

### Security
- Reinforced the project-wide invariant that secret/env var values are never emitted in trust-related output or logs; only names may be shown.


## [v1.2.0] - 2026-03-05
### Changed
- Refactored `pack` and `publish` flows in Feature13 to use the registry abstraction and source-mode path consistently.
- Improved packaging/publishing reliability through shared backend handling and updated test coverage.

### Deprecated
- Feature12 legacy registry path/tests were deprecated and documented to prevent accidental re-enable.


## [v1.1.0] - 2026-03-05
### Added
- Implemented `kinnoo pack` command for packaging projects.
- Enhanced `kinnoo install` with improved functionality and support for packaged projects.

## [v1.0.0] - 2026-02-25
### Added
- Initial release.
- Implemented all MVP features:
  - `kinnoo init` for project initialization.
  - `kinnoo run` for running projects.
  - `kinnoo install` for installing dependencies.
