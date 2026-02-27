# SWE Handoff — Feature8 Packaging Robustness (Tests)

## Scope
This handoff is for implementing the new Feature8 tests already defined in `TESTS.txt`:

- `test65` → AC1 (transitive dependency wheels included)
- `test66` → AC2 (canonical `.kno` zip format)
- `test67` → AC3 (wheel build failure is non-fatal with warning)
- `test68` → AC4 (install fallback to PyPI for missing wheels)
- `test69` → AC5 (offline install succeeds when wheel set is complete)
- `test70` → AC6 (platform-specific wheel warning)

Related tasks in `TASKS.txt`:

- `task42` → `test65`
- `task43` → `test66`
- `task44` → `test67`
- `task45` → `test68`
- `task46` → `test69`
- `task47` → `test70`

## Test Design Principles (must follow)
1. Use pinned dependency versions for deterministic behavior.
2. Validate true dependency resolution behavior (direct + transitive), not only superficial command success.
3. Prefer small, realistic fixtures over mocks for archive/wheel/install workflows.
4. Keep tests independent and hermetic (`tmp_path`, isolated env vars, explicit cleanup).
5. Assert user-facing warnings/messages that are part of ACs.

## Recommended Fixture Dependencies (Pinned)

### Primary transitive fixture (for AC1/AC5)
Use these in generated fixture `requirements.txt`:

```txt
requests==2.31.0
httpx==0.27.0
```

Why:
- `requests` pulls transitives like `urllib3`, `certifi`, `charset-normalizer`, `idna`.
- `httpx` pulls `httpcore`, `anyio`, and related transitives.
- Both are common, stable, and exercise meaningful dependency trees.

### Platform-specific wheel fixture (for AC6)
Use:

```txt
orjson==3.10.6
```

Why:
- Commonly provides platform-tagged wheels, suitable for portability warning detection.

## Proposed Test Module Layout
Create or extend:

- `tests/test_pack_robustness.py` (for test65, test66, test67, test70)
- `tests/test_cli_install.py` (for test68, test69)

Keep helper utilities local to the test module or `tests/conftest.py` only if reused by multiple files.

## Implementation Notes by Test

### test65 — transitive wheels included
- Build a fixture agent with pinned dependencies above.
- Run `kinnoo pack`.
- Inspect `.kno` archive wheel entries.
- Assert direct wheels and representative transitives are present.
- Prefer asserting a meaningful subset (e.g., `requests`, `httpx`, `urllib3`, `certifi`, `httpcore`, `anyio`) rather than every wheel to reduce brittleness.

### test66 — zip canonicalization
- Run `kinnoo pack` and verify resulting `.kno` is zip-structured.
- Avoid extension-only checks; verify archive type via zip inspection behavior.
- Run `kinnoo install` with produced archive and assert success.

### test67 — non-fatal wheel failure
- Use one valid pinned dependency plus one intentionally invalid package name.
- Assert:
	- pack still exits successfully,
	- archive is created,
	- warning names failed dependency.
- Ensure this test validates warning semantics, not just command output existence.

### test68 — PyPI fallback for missing wheel
- Start with a valid packed archive.
- Remove one required wheel from archive contents before install.
- Install with network enabled.
- Assert warning is printed and installation still succeeds.
- Verify installed environment can import/use the previously missing dependency.

### test69 — offline install with complete wheel set
- Use complete transitive wheel archive from pinned fixture.
- Run install in a no-network context (monkeypatch network calls or enforce pip flags/env so network access is disallowed in test environment).
- Assert install and run succeed without fallback warning.
- This is the critical correctness test for AC5.

### test70 — platform-specific wheel warning
- Pack fixture containing `orjson==3.10.6`.
- Assert portability warning text is present.
- Assert archive creation still succeeds.

## Suggested Helper Utilities
- `create_fixture_agent(tmp_path, requirements_lines)`
- `run_kinnoo_pack(agent_dir)`
- `list_archive_wheels(kno_path)`
- `remove_wheel_from_archive(kno_path, wheel_predicate)`
- `run_kinnoo_install(kno_path, target_dir=None, env=None)`

Keep helper names descriptive and avoid hidden global state.

## Risk Areas / Pitfalls
- Over-asserting exact full wheel set may create flaky tests across packaging tool updates; assert required subset + behavior.
- Offline test strategy must be deterministic; do not rely on machine-level firewall state.
- Warning text assertions should target stable substrings required by ACs.
- Ensure tests do not leak caches or environment state between runs.

## Definition of Done for SWE implementation
1. Add/implement tests for `test65`–`test70` in the specified automation paths.
2. Keep dependency versions pinned exactly as declared above unless TechLead approves changes.
3. Run targeted tests first, then broader regression scope.
4. Update task statuses to `in-progress` then `needs-review` when complete.
5. Ensure no secrets or sensitive values are logged in test output.
