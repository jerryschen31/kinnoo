# Feature5: kinnoo pack — Agent Packaging

## Summary

- **Goal:** Implement a CLI command `kinnoo pack` that packages an agent project (code, manifest, dependencies) into a distributable archive with a `.kno` extension.
- **Archive Contents:** Must include `kinnoo.yaml`, entrypoint, `requirements.txt`, and any additional files declared in the manifest. Also, pre-built wheel files for all dependencies.
- **Format:** Archive is a zip (`.tar.gz`) with a `.kno` extension, inspectable with standard tools.
- **Usage:** `kinnoo pack <agent-dir>` creates the archive. Running without arguments prints usage instructions.
- **Validation:** Manifest must be validated before packaging; errors abort the process.
- **Safety:** Packing from inside the agent directory is forbidden (prints a clear error).
- **Integration:** Archive produced must be accepted by `kinnoo install` for installation.

## Relation to Previous Features

- **Depends on:** feature3 (`kinnoo run`), which ensures agents are runnable from source with a standard manifest, entrypoint, and dependency management.
- **Builds on:** feature1 (manifest schema/validation) and feature2 (project scaffolding), as packaging requires a valid manifest and a predictable project structure.
- **Prepares for:** feature6 (`kinnoo install`), which will consume the `.kno` archive.

## Implementation Difficulty

### Key Steps

1. **Manifest Validation:** Reuse the validator from feature1.
2. **File Collection:** Gather all required files (manifest, entrypoint, requirements.txt, and any others listed in the manifest).
3. **Dependency Packaging:** Use `pip wheel` or `pip download` to collect wheel files for all dependencies in `requirements.txt`.
4. **Archive Creation:** Bundle everything into a `.kno` (zip/tar.gz) archive.
5. **CLI UX:** Handle argument parsing, error messages, and usage instructions.
6. **Safety Checks:** Prevent running from inside the agent directory.

### Complexity Assessment

- **Technical Complexity:** Moderate. All required tools (`pip`, `zip`/`tarfile`, Python stdlib) are well-documented and stable. No advanced algorithms or novel techniques required.
- **Integration:** Needs careful handling of file paths, error reporting, and manifest-driven logic, but nothing outside the skillset of a senior engineer or a capable AI agent.
- **Testing:** Straightforward to test with unit and integration tests (e.g., create a sample agent, pack it, inspect archive contents).

### Suitability of Free-Tier Model (GPT-4.1)

- **Coding Tasks:** GPT-4.1 is more than sufficient for this feature. The tasks involve standard Python scripting, CLI argument parsing, file I/O, subprocess management, and error handling.
- **No Need for Pro Tier:** There’s no need for advanced reasoning, huge context windows, or proprietary APIs. The logic is clear, and the requirements are well-scoped.
- **Best Practices:** As long as the agent follows the project’s coding standards (modular code, error handling, documentation, tests), GPT-4.1 can handle the implementation.

## Conclusion

Feature5 is a well-scoped, moderately complex packaging task that builds directly on the foundation laid by features 1–3. It is highly suitable for implementation by a free-tier model like GPT-4.1, provided the agent follows best practices and project guidelines. No advanced AI capabilities are required beyond what GPT-4.1 offers.
