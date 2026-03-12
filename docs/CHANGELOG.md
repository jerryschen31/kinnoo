# Changelog

All notable changes to this project will be documented in this file.


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
