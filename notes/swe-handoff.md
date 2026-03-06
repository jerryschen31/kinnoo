# SWE Handoff — Feature13 Pack/Publish Refactor

## Scope
Implement feature13 end-to-end with archive-first packaging and mock-registry publishing:
- `kinnoo pack` writes to `~/.kinnoo/archive/<agent>/<version>/<agent>.kno` by default.
- `kinnoo publish <agent-name>` resolves latest local archived artifact and publishes to `registry-scratch/jerry/<agent>/<version>/<agent>.kno`.
- `install`, `list`, `search` support local/remote source behavior as specified in feature13 ACs.

## Recommended Implementation Order
1. `task78` Prompt before overwriting existing `.kno` archive
2. `task79` Add `--bump` version automation to `kinnoo pack`
3. `task80` Define archive and registry storage abstractions
4. `task81` Refactor pack default archive destination
5. `task82` Standardize pack output and overwrite confirmation
6. `task83` Refactor publish CLI to agent-name source
7. `task84` Implement publish mock registry target and untagged rollover
8. `task85` Install by registry name/version using mock backend
9. `task86` Refactor `list` with default local and source flags
10. `task87` Refactor `search` with default local and source flags
11. `task88` Preserve file-path install compatibility
12. `task90` Harden source-mode CLI validation and errors
13. `task89` Document refactor and migration guidance

## Task → Test Mapping (exact)
- `task78` → `test105`
- `task79` → `test106`
- `task80` → `test107`
- `task81` → `test107`
- `task82` → `test108`
- `task83` → `test109`, `test111`
- `task84` → `test110`
- `task85` → `test112`, `test113`
- `task86` → `test114`
- `task87` → `test115`
- `task88` → `test116`
- `task89` → `test117`
- `task90` → `test118`

## Required Contracts (must not drift)
- Overwrite prompt format:
	- `(archive.kno) already exists - are you sure you want to overwrite? (y/n): `
	- Use concrete archive filename in place of `archive.kno`.
- Pack success output always includes:
	- `[kinnoo pack] Agent version: <version #>`
- Publish source/target semantics:
	- Source from local archive latest when using `kinnoo publish <agent-name>`
	- Target path: `registry-scratch/jerry/<agent>/<version>/<agent>.kno`
	- Existing tagged publish version rolls old artifact to `untagged-<n>`.
- Source-mode command behavior:
	- `kinnoo list` defaults to local archive; `--local` same as default; `--remote` uses mock registry.
	- `kinnoo search` defaults to local archive; `--local` local; `--remote` mock registry.
	- `kinnoo install <name>` latest from mock registry; `kinnoo install <name>==<version>` exact from mock registry.
	- `kinnoo install <file-path/file.kno>` remains backward compatible.

## CLI Validation Requirements
- Reject invalid/ambiguous argument combinations with deterministic non-zero errors.
- Enforce mutual exclusivity for `--local` and `--remote` where applicable.
- No silent fallback to unintended source when input is invalid.

## Done Criteria
- Tasks `task78`–`task90` implemented and marked `needs-review`.
- Tests `test105`–`test118` implemented and passing.
- `python3 src/validate_project_manifests.py` passes.
