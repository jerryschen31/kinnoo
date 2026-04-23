# Task 514 Notes

## User Prompt (verbatim)
Create a new feature120 in FEATURES.txt titled "UAT 3 - fixes". The description should be around "3rd round of User Acceptance Testing ... UI tweaks and bug fixes as necessary." Add what you just fixed (tenant-qualified install/fetch selector and remote checksum verification behavior) as a new task514 in TASKS.txt and add associated tests you created to TESTS.txt. Set statuses to needs-review. Put my prompt and your response verbatim into notes/tasks/task514-notes.md.

## Assistant Response (verbatim)
Implemented the requested fixes and test coverage for tenant-qualified selectors and remote checksum verification behavior across CLI, server, and web paths.

What was fixed:
- Updated selector parsing and resolution to support tenant-qualified targets in install/fetch flows.
- Corrected web modal install command exact-version syntax to use `==`.
- Added remote checksum metadata support so archive verification works even when temp downloads have no adjacent sidecar.
- Added/updated regression tests for parser behavior and install/fetch tenant-qualified selector flows.

Validation:
- Targeted pytest suites for parser/install/fetch changes passed.
- Targeted web vitest suites passed for modal/registry command behavior.

## Follow-up Prompt and Fix

### User Prompt (verbatim)
Yes, update docs/security-model.md clarifying this trust model and expected behavior for strict install when sidecars are absent.
Also add notes of my prompt and your fix as a new section in notes/tasks/task514-notes.md

Finally, I ran kinnoo install --strict and it works, but you need to add a [kinnoo install] info line stating that embedded signature is verified, because it's currently missing in the output info:

```
% kinnoo install --strict test-agent-phase14-js-2
[kinnoo install] Resolved registry selector 'test-agent-phase14-js-2' to '/var/folders/38/32gjhl955tn87pt52x6g9hk80000gn/T/tmpeidgmtgz.kno' (remote)
[kinnoo install] Archive checksum verified.
[kinnoo install] Detached signature artifacts not found; falling back to embedded META-INF/signature.json verification.
[kinnoo install] Install summary:
- Agent: test-agent-phase14-js-2
- Version: 0.1.1
- Runtime Type: one-shot
- Dependencies: (none)
- Env Vars: (none)
- Permissions: (none declared)
Continue with install? [y/N]: y
```

I would recommend:

```
% kinnoo install --strict test-agent-phase14-js-2
[kinnoo install] Resolved registry selector 'test-agent-phase14-js-2' to '/var/folders/38/32gjhl955tn87pt52x6g9hk80000gn/T/tmpeidgmtgz.kno' (remote)
[kinnoo install] Archive checksum verified.
[kinnoo install] Detached signature artifacts not found; falling back to embedded META-INF/signature.json verification.
[kinnoo install] Embedded signature verified.
[kinnoo install] Install summary:
- Agent: test-agent-phase14-js-2
- Version: 0.1.1
- Runtime Type: one-shot
- Dependencies: (none)
- Env Vars: (none)
- Permissions: (none declared)
Continue with install? [y/N]: y
```

### Assistant Fix Summary
- Updated `install --strict` fallback flow to pre-verify embedded signature metadata when detached sidecars are absent, and emit `[kinnoo install] Embedded signature verified.` before the install summary.
- Kept strict trust gates intact: strict mode still fails if embedded signature or key resolution fails.
- Avoided duplicate success messaging by suppressing the later embedded-signature success line when pre-install verification already emitted it.
- Added regression assertions to ensure embedded-signature success line appears before `[kinnoo install] Install summary:` in strict fallback path.
- Updated security documentation in `docs/security-model.md` to clarify embedded vs detached signature roles and strict install fallback behavior when sidecars are absent.