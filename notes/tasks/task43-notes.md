# SWE Scratch Notes

Date: 2026-02-27

## Task43 Summary — Canonical `.kno` ZIP Format + test66

### Implementation
- Verified runtime behavior already used ZIP semantics in both:
  - `src/kinnoo/pack_command.py` (`zipfile.ZipFile(..., "w")`)
  - `src/kinnoo/install_command.py` (`zipfile.ZipFile(..., "r")` with `BadZipFile` handling)
- Added canonical format regression test in `tests/test_pack_robustness.py`:
  - `test_kno_zip_format_is_canonical` (test66)
  - Asserts `.kno` produced by `kinnoo pack` is a real ZIP (`zipfile.is_zipfile(...)`)
  - Asserts `kinnoo install` succeeds from the produced `.kno` archive
- Updated user-facing docs to align with ZIP semantics:
  - `README.md` packaging-format section
  - `docs/manifest-schema-reference.md` archive-format note

### Validation
- Targeted feature8 tests:
  - `python3 -m pytest tests/test_pack_robustness.py::test_pack_includes_transitive_wheels_for_pinned_deps tests/test_pack_robustness.py::test_kno_zip_format_is_canonical`
  - Result: `2 passed`
- Focused regression sweep:
  - `python3 -m pytest tests/test_pack.py tests/test_cli_install_extract.py tests/test_pack_robustness.py`
  - Result: `10 passed`
- Manifest validation:
  - `python3 scripts/validate_project_manifests.py`
  - Result: `Validation passed: manifests are consistent`

### Task Status
- `task43` updated to `needs-review` in `TASKS.txt`.
