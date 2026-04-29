# Task500 Notes

## Summary
- Added external-subject identity mapping persistence helpers in `server/storage/sqlite_auth_store.py`.
- Updated OIDC web callback flow to reuse/create mapped internal users and persist provider identity links.
- Updated publish ownership resolution to map OIDC subjects to internal UUID owners and persist deterministic tenant-owner linkage.
- Added integration coverage in `server/tests/test_publish.py::test_feature118_identity_mapping_and_publish_ownership`.

## Teaching Notes
- Keep identity ownership canonical by storing provider subject as an attribute and internal UUID as the primary owner key.
- Deterministic mapping logic should be centralized so both web and CLI auth paths resolve to the same internal identity contract.
- Preserve backward compatibility by keeping existing metadata fields while adding richer ownership context fields.
