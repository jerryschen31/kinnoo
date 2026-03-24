## Phase 4 (V4) Plan: OpenClaw + JS/TS Agent Support

This plan formalizes Phase 4 as features 31-41 and aligns with the final section in [notes/phases/phase4-openclaw-support-thoughts.md](notes/phases/phase4-openclaw-support-thoughts.md):

V4 Final Feature Set: JS/TS Runtime & Security Hardening

### Phase 4 Goals
- Add generic JS/TS agent runtime support (not only OpenClaw).
- Add standalone OpenClaw compatibility (one-shot + daemon), without taking over full gateway orchestration.
- Raise security posture for third-party agent install and execution.
- Keep backwards compatibility for existing Python agents and workflows.

### Final Feature List (31-41)

#### feature31: Node.js Runtime Support (Foundation)
What it delivers:
- First-class `runtime.language: nodejs` support.
- Node-based run/install contract with package manager awareness.
- Node environment preflight checks (version + toolchain availability).

Why now:
- This is the base dependency for most remaining V4 features.
- Enables generic JS/TS ecosystem support beyond OpenClaw.

Design notes:
- Start with `.js/.mjs` execution path and defer TS transpilation pipeline.
- Preserve Python behavior unchanged.

#### feature32: Daemon Runtime Type + Process Controls
What it delivers:
- `runtime.type: daemon` lifecycle support.
- Start/stop process management with PID/state handling.
- Operator UX controls for `attach` and `logs`.

Why now:
- OpenClaw and similar agent systems often need long-running processes.
- Bridges gap between one-shot commands and service-like operation.

Design notes:
- This is process lifecycle management, not full OpenClaw gateway management.
- Reuse supervisor/health-check architecture already in repo.

#### feature33: Manifest Schema Extensions for OpenClaw/JS Agents
What it delivers:
- `runtime.package_manager`, `channels`, `skills`, and `state_dirs` schema support.
- OpenClaw-aware validation path under `framework: openclaw`.

Why now:
- Provides durable schema contract for scaffold/import/runtime and packaging behavior.

Design notes:
- Keep schema generic so it works for future JS/TS frameworks.
- New fields are optional and non-breaking by default.

#### feature34: OpenClaw Scaffold Template
What it delivers:
- `kinnoo init --framework openclaw` scaffolding with OpenClaw conventions.
- Runnable starter structure including identity and skill files.

Why now:
- Low-friction onboarding path for new OpenClaw-compatible projects.

Design notes:
- Template remains standalone and package-oriented.
- Does not depend on external `openclaw` CLI binary at init-time.

#### feature35: Mutable State Directories in Pack/Install
What it delivers:
- First-class `state_dirs` snapshot/restore semantics.
- Optional exclusion patterns for selective memory packaging.

Why now:
- OpenClaw-style memory requires mutable state handling distinct from immutable assets.
- Useful for many non-OpenClaw agents too.

Design notes:
- Preserve compatibility with existing `assets` behavior.
- Encourage safe defaults around overwrite and sensitive state handling.

#### feature36: OpenClaw Import Detection & Manifest Inference
What it delivers:
- Analyzer-backed detection of OpenClaw projects.
- Inference of Node runtime fields, skills, and state directories.
- Confidence/evidence-based import output.

Why now:
- Unlocks migration path for existing OpenClaw projects into kinnoo.

Design notes:
- Use strong/medium signal weighting (openclaw.json, package deps, SOUL.md, skills, memory).
- Keep warning-first UX for ambiguous inference.

#### feature37: Node.js Dependency Audit & Lifecycle Script Controls
What it delivers:
- Audit visibility during install for Node dependency risk.
- Policy controls for CVE severity gating and install script execution.

Why now:
- Install-time package scripts are a high-risk execution path in Node ecosystems.

Design notes:
- Security gate should be configurable for local vs CI contexts.
- Keep Python install path unaffected.

#### feature38: JS/TS Static Security Sweep
What it delivers:
- Static sweep expansion to JS/TS/JSON files.
- Detection for secrets and dangerous execution/config patterns.

Why now:
- Existing trust baseline primarily targets Python paths.
- V4 needs equivalent controls for Node-based agents.

Design notes:
- Start warning-first to balance security signal and false positives.
- Maintain no-secret-value output invariant.

#### feature39: Manifest Permissions Model + Sandbox Execution
What it delivers:
- Explicit permission declarations in manifest.
- Install-time permission disclosure/consent.
- `run --sandbox` enforcement path.

Why now:
- Creates transparent contract between publisher intent and runtime capability.
- Foundation for runtime enforcement and monitoring.

Design notes:
- Prioritize practical enforceable controls first (filesystem/network/shell).
- Applies across Python and Node where possible.

#### feature40: Archive Signing & Publisher Verification
What it delivers:
- Key generation + archive signing workflow.
- Signature verification at install.
- Publisher authenticity model complementing checksums.

Why now:
- Current checksum story covers integrity only, not identity/authenticity.

Design notes:
- Keep signing module isolated for future trust-policy and key-rotation work.
- Integrate with registry metadata over time.

#### feature41: Runtime Behavior Monitoring & Kill Switch
What it delivers:
- Runtime telemetry for process/network/filesystem behavior.
- Policy-driven kill switch on violations.
- Resource limits and dry-run tracing path.

Why now:
- Provides post-install defense layer if static/install-time checks miss threats.

Design notes:
- Build cross-platform baseline first; deeper syscall instrumentation can follow.
- Integrates with permissions model from feature39.

### Dependencies and Sequencing
- Foundation track: feature31, feature35, feature39, feature40
- Runtime/schema track: feature32, feature33
- OpenClaw UX track: feature34, feature36
- Security hardening track: feature37, feature38, feature41

Recommended delivery waves:
1. Wave 1: feature31 + feature35 + feature39 + feature40
2. Wave 2: feature32 + feature33 + feature37 + feature38
3. Wave 3: feature34 + feature36 + feature41

### Explicitly Deferred Out of V4
- Full OpenClaw gateway lifecycle orchestration.
- Channel onboarding UX (for example QR pairing flows).
- Remote ingress/tunnel management.
- Secret-proxy/channel-vault platform work.
- Full TS transpilation pipeline as a required runtime path.

### Risk and Scope Notes
- Feature31 and feature39 are high-risk due to broad cross-cutting impact.
- Feature41 should be delivered incrementally to avoid platform-specific instability.
- Keep all V4 changes regression-tested against existing Python commands and archived agents.
- Maintain V4 focus on portable packaged agents; avoid host-bound gateway expansion in this phase.
