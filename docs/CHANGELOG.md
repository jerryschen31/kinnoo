# Changelog

All notable changes to this project will be documented in this file.


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
