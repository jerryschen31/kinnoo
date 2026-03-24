# Task229 - feature28 registry backend protocol + local backend refactor

## Summary
- Added a dedicated backend-contract module at src/kinnoo/registry_backend.py with a runtime-checkable RegistryBackend protocol.
- Refactored protocol ownership in src/kinnoo/registry.py to import the contract from the new module (instead of defining it inline).
- Introduced LocalRegistryBackend in src/kinnoo/registry_backends.py as the canonical local implementation.
- Preserved compatibility by keeping LocalFilesystemRegistryBackend as a backward-compatible alias class that inherits from LocalRegistryBackend.
- Added list_agents(...) to local backend implementation for tenant-aware protocol compatibility while preserving current single-tenant local behavior.
- Exported LocalRegistryBackend from src/kinnoo/__init__.py for package-level access.
- Added mapped test327 in tests/test_registry.py as test_registry_backend_protocol.

## Tests and results
- python3 -m pytest tests/test_registry.py::test_registry_backend_protocol -> 1 passed

## Bug/error notes
- No bug/error class required iterative fixes for task229.
- Same bug/error class fix attempts: 0 (cap: 5).

## Teaching notes
- Protocol-first refactors reduce coupling: command/service layers depend on behavior contracts, not concrete storage classes. This is the same architectural move you use when evolving from local filesystems to networked services.
- Backward-compatible aliasing is a practical migration technique: introducing LocalRegistryBackend while retaining LocalFilesystemRegistryBackend avoids breaking older imports during staged rollouts.
- Adding a tenant parameter now (even if ignored for local) is a forward-compatibility seam. This keeps API signatures stable when multi-tenant remote backends are added, minimizing churn in callers.
- Runtime protocol checks in tests help catch shape drift early. A small contract test is valuable when multiple backends (local today, remote next) must remain interchangeable.
