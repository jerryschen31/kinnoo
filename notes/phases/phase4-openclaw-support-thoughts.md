## Plan: OpenClaw Agent Support in Kinnoo

### TL;DR

**Feasible.** Supporting OpenClaw agents requires **6 new features (feature31–feature36)** that build a Node.js runtime layer, extend the manifest schema, add scaffold/import/pack support for OpenClaw conventions, and introduce daemon process management. The foundation is generic Node.js runtime support which also benefits future JS/TS agent frameworks.

---

### Feasibility Assessment

**OpenClaw** is an open-source personal AI assistant (TypeScript/Node.js, Node ≥22, 318k GitHub stars). It uses:
- A gateway daemon architecture (WebSocket control plane + channels like WhatsApp/Telegram/Discord)
- Skills as `SKILL.md` folders (AgentSkills-compatible YAML frontmatter + instructions)
- Persistent `memory/` folder for agent state
- `openclaw.json` for config, `package.json` for Node.js deps

**Kinnoo today** is Python-only: `python <entrypoint> "<input>"`, pip/venv, no Node.js anywhere in the codebase.

| Gap | Description |
|---|---|
| Runtime language | Only Python; need Node.js |
| Dependency manager | Only pip/venv; need npm/pnpm + node_modules |
| Runtime type | Only one-shot + mcp-server; need daemon for long-running |
| State management | Only static assets; need mutable state dirs (memory/) |
| Import detection | Only Python AST; need package.json/SKILL.md/openclaw.json |

**Verdict**: All gaps are addressable with well-scoped features. No blocking technical unknowns.

---

### Proposed Features

#### feature31: Node.js Runtime Support (Foundation)
Add Node.js as a first-class runtime language alongside Python. Entrypoint contract: `node <entrypoint> "<input>"`. npm install in agent directory (node_modules is the venv equivalent). Exclude node_modules from archives; include package.json + lockfile for reproducibility.
- **Files**: [src/kinnoo/schema.py](src/kinnoo/schema.py), [src/kinnoo/run_command.py](src/kinnoo/run_command.py), [src/kinnoo/install_command.py](src/kinnoo/install_command.py), [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py), [src/kinnoo/validator.py](src/kinnoo/validator.py), [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py)
- **Dependencies**: None (foundational; blocks everything else)

#### feature32: Daemon/Long-running Process Support
Add `"daemon"` runtime type. `kinnoo run` starts the process with PID management; `kinnoo stop` sends SIGTERM for graceful shutdown. Reuses existing [src/kinnoo/supervisor.py](src/kinnoo/supervisor.py) and [src/kinnoo/health_check.py](src/kinnoo/health_check.py). Works for both Python and Node.js agents.
- **Files**: [src/kinnoo/schema.py](src/kinnoo/schema.py), [src/kinnoo/run_command.py](src/kinnoo/run_command.py), [src/kinnoo/cli.py](src/kinnoo/cli.py), [src/kinnoo/supervisor.py](src/kinnoo/supervisor.py)
- **Dependencies**: feature31

#### feature33: OpenClaw Manifest Extensions
Extend kinnoo.yaml with: `runtime.package_manager` (npm/pnpm), `channels` (declared integrations), `skills` (SKILL.md paths), `state_dirs` (mutable folders like memory/). Framework-agnostic schema — `framework: openclaw` triggers OpenClaw-specific validation.
- **Files**: [src/kinnoo/schema.py](src/kinnoo/schema.py), [src/kinnoo/validator.py](src/kinnoo/validator.py), [docs/manifest-schema-reference.md](docs/manifest-schema-reference.md)
- **Dependencies**: feature31

#### feature34: OpenClaw Agent Scaffold Template
`kinnoo init my-agent --framework openclaw` generates: `package.json`, `index.mjs` (real API integration, not hello world), `openclaw.json`, `skills/default/SKILL.md`, `memory/`, `AGENTS.md`, `SOUL.md`. Runnable with `kinnoo run my-agent/ "hello"` after setting API keys.
- **Files**: [src/kinnoo/templates.py](src/kinnoo/templates.py), [src/kinnoo/init_command.py](src/kinnoo/init_command.py)
- **Dependencies**: feature31, feature33

#### feature35: Mutable State Folders (memory/) in Pack/Install
New `state_dirs` manifest field for mutable directories. Pack captures current contents as snapshot. Install restores snapshot (warns if state already exists, `--force` to overwrite). Distinct from `assets` (immutable). Useful for any agent framework, not just OpenClaw.
- **Files**: [src/kinnoo/schema.py](src/kinnoo/schema.py), [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py), [src/kinnoo/install_command.py](src/kinnoo/install_command.py), [src/kinnoo/validator.py](src/kinnoo/validator.py)
- **Dependencies**: None (parallel with feature32)

#### feature36: OpenClaw Agent Import Support
`kinnoo import` detects existing OpenClaw projects via: `package.json` with openclaw dep (high confidence), `openclaw.json` (high), `SKILL.md` files (medium), `memory/` directory (state_dirs candidate). Generates complete kinnoo.yaml wrapping existing structure.
- **Files**: [src/kinnoo/analyzer.py](src/kinnoo/analyzer.py), [src/kinnoo/import_command.py](src/kinnoo/import_command.py)
- **Dependencies**: feature31, feature33, feature35

---

### Dependency Graph & Implementation Order

```
feature31 (Node.js Runtime) ──┬── feature32 (Daemon Support)
                               ├── feature33 (Manifest Ext.) ──┬── feature34 (Scaffold)
                               │                                └── feature36 (Import)
                               └───────────────────────────────── feature35 (State Folders) ── feature36
```

1. **feature31** (Node.js Runtime) — *blocks everything*
2. **feature32** (Daemon) + **feature35** (State Folders) — *parallel, independent*
3. **feature33** (Manifest Extensions) — *depends on 31*
4. **feature34** (Scaffold) — *depends on 31 + 33*
5. **feature36** (Import) — *depends on 31 + 33 + 35*

---

### Key Design Decisions
- **Standalone agent model**: OpenClaw agents in kinnoo are self-contained Node.js projects following OpenClaw conventions, not full gateway installations
- **Generic Node.js first**: feature31 is framework-agnostic — benefits future JS/TS agent frameworks beyond OpenClaw
- **node_modules excluded from archives**: Pack includes package.json + lockfile only; npm install runs at install time
- **state_dirs as new concept**: Separate from assets (mutable vs immutable); useful for any framework

### Open Questions
1. **npm vs pnpm**: Recommend `runtime.package_manager` in manifest, default to npm
2. **OpenClaw version pinning**: Recommend pinning to latest stable at scaffold time
3. **TypeScript support**: Recommend deferring `.ts` entrypoints; start with `.mjs/.js` only


## Follow-up Q&A (Verbatim)

Great questions. Here's my analysis on both.

---

## 1. What is a "full gateway installation" and is it worth supporting?

**What it is**: The full OpenClaw deployment is a **persistent daemon process** (Node >=22) that:
- Runs a WebSocket control plane on `127.0.0.1:18789`
- Maintains live connections to messaging channels (WhatsApp via Baileys, Telegram via grammY, Discord, Slack, Signal, iMessage, etc.)
- Manages a "Pi agent" (the AI brain) that calls tools, browses the web, executes shell commands
- Has a companion macOS app, iOS/Android node apps, a web UI, and browser control (CDP)
- Stores credentials, session transcripts, agent workspace, skills, and memory on disk under `~/.openclaw/`
- Manages its own plugin system, cron scheduler, webhooks, and multi-agent routing

**What it would take to support**: This is a fundamentally different beast from what kinnoo manages today. Supporting it would require:
- **Gateway lifecycle management**: Starting/stopping `openclaw gateway --port 18789 --install-daemon`, health monitoring via the WS protocol, launchd/systemd service registration
- **Channel credential orchestration**: Configuring WhatsApp pairing, Telegram bot tokens, Discord tokens - all stored in `~/.openclaw/credentials/`
- **WS-based integration**: Communicating with the gateway via its typed WebSocket API (connect handshake -> req/res frames) rather than simple stdio
- **Host-level permissions**: Browser control, filesystem access, shell execution - the gateway has *full host access* by design
- **Multi-agent routing**: The gateway can run multiple agents with different workspaces and tool policies

**Is it worth it?** My recommendation: **Not as a near-term feature.** Here's the reasoning:

| Factor | Assessment |
|---|---|
| Complexity | Very high - it's essentially wrapping an entire operating system-level daemon with its own security model, not a portable agent |
| Portability | Low - a full gateway is inherently tied to a host machine (WhatsApp sessions, browser profiles, device pairings) |
| kinnoo's value prop | kinnoo is about **packaging, distributing, and safely running portable agents**. A full gateway install is neither portable nor packageable |
| User demand | The standalone-agent model (skills + memory + API calls) covers the 80% use case. People who need a full gateway already have `openclaw onboard` |

**What I'd recommend instead**: A future `feature37: kinnoo gateway-bridge` that lets a kinnoo-packaged OpenClaw agent *register itself as a skill* with an existing OpenClaw gateway installation. This is lighter - kinnoo manages the agent, OpenClaw manages the infrastructure. But this is a "Phase 3" concern, well after features 31-36.

---

## 2. Security-focused features for safer OpenClaw agent distribution

This is where kinnoo can provide **massive** value over raw OpenClaw. Here's why:

**OpenClaw's security model assumes a trusted operator boundary** - their own docs say "one trusted operator boundary per gateway" and "treat third-party skills as untrusted code. Read them before enabling." But in practice, OpenClaw skills are just SKILL.md folders downloaded via `clawhub install <skill-slug>`, with npm lifecycle scripts that **can execute arbitrary code during install**. There's no signature verification, no dependency audit, no sandboxed execution for untrusted skills.

Here are the security features kinnoo should add:

### feature37: Node.js Dependency Audit on Install

**Problem**: npm packages can contain malware. `npm install` executes `preinstall`/`postinstall` lifecycle scripts - these can run arbitrary code the moment you install them. OpenClaw's own docs warn about this but provide no automated protection.

**What kinnoo provides**:
- Run `npm audit` automatically during `kinnoo install` and surface CVE counts (critical/high/moderate/low)
- Block install if critical CVEs detected (overridable with `--allow-vulnerable`)
- Detect and warn about `preinstall`/`postinstall` lifecycle scripts in package.json and transitive dependencies
- Option: `--ignore-scripts` flag that passes `npm install --ignore-scripts` to prevent lifecycle script execution
- Log exact dependency tree at install time for reproducibility auditing

**Files**: [src/kinnoo/install_command.py](src/kinnoo/install_command.py)

### feature38: Static Analysis Security Sweep for Node.js Agents

**Problem**: kinnoo's existing `code_sweep.py` only scans Python files. Node.js agents need equivalent protection.

**What kinnoo provides**:
- Extend secret scanning to `.js`/`.mjs`/`.ts`/`.json` files: detect hardcoded API keys, tokens, credentials
- Scan for dangerous Node.js patterns: `child_process.exec()`, `eval()`, `Function()` constructor, `require('fs').writeFileSync` on sensitive paths, network calls to suspicious destinations
- Detect `openclaw.json` with dangerous flags enabled (any `dangerously*` config key, `tools.exec.security: "off"`, `gateway.bind` not loopback)
- Warn about overly permissive skills (`system.run` capability without restrictions)
- Flag `memory/` contents that contain credential-like patterns before packing

**Files**: [src/kinnoo/code_sweep.py](src/kinnoo/code_sweep.py)

### feature39: Permission Declaration & Runtime Sandboxing

**Problem**: Raw OpenClaw agents get full host access by default - shell execution, filesystem read/write, network, browser control. There's no way to know what an agent *needs* before running it, and no way to constrain it.

**What kinnoo provides**:
- New `permissions` field in kinnoo.yaml declaring what the agent requires:
    ```yaml
    permissions:
        network: true          # can make outbound HTTP requests
        filesystem: read-only  # read-only | read-write | workspace-only | none
        shell: false           # can execute shell commands
        browser: false         # can control a browser
        env_access:            # which env vars the agent reads
            - ANTHROPIC_API_KEY
            - TELEGRAM_BOT_TOKEN
    ```
- `kinnoo install` displays permission summary and requires explicit confirmation: "This agent requests: network access, filesystem read-write, shell execution. Continue? [y/N]"
- `kinnoo run --sandbox` executes in a restricted environment (Docker container or firejail) that enforces declared permissions
- Permission violations logged and reported

**Files**: [src/kinnoo/schema.py](src/kinnoo/schema.py), [src/kinnoo/validator.py](src/kinnoo/validator.py), [src/kinnoo/run_command.py](src/kinnoo/run_command.py), [src/kinnoo/install_command.py](src/kinnoo/install_command.py)

### feature40: Archive Signing & Publisher Verification

**Problem**: kinnoo currently has SHA256 checksums for integrity (corruption detection), but no **authenticity** verification. Anyone can produce a `.kno` archive claiming to be any agent. OpenClaw's ClawHub has no signing mechanism either.

**What kinnoo provides**:
- `kinnoo pack --sign` signs the archive with the publisher's private key (Ed25519)
- `kinnoo install` verifies the signature against the publisher's registered public key
- `kinnoo keygen` generates a keypair; public key publishable to the registry
- Archives without signatures get a prominent "UNVERIFIED PUBLISHER" warning at install time
- Registry stores publisher public keys and maps them to agent names (prevents name squatting after initial publish)

**Files**: new `src/kinnoo/signing.py`, [src/kinnoo/pack_command.py](src/kinnoo/pack_command.py), [src/kinnoo/install_command.py](src/kinnoo/install_command.py)

### feature41: Runtime Behavior Monitoring & Kill Switch

**Problem**: Even after install-time checks, a malicious agent can behave differently at runtime. OpenClaw agents with shell access can exfiltrate data, install backdoors, or modify system files. OpenClaw provides no post-launch monitoring for untrusted agents.

**What kinnoo provides**:
- Monitor subprocess activity during `kinnoo run`: capture syscall-level events (network connections, file writes outside workspace, process spawning)
- Automatic kill if agent violates declared permissions (e.g., opens a network socket when `permissions.network: false`)
- Resource limits: CPU time, memory, wall-clock timeout (prevents crypto mining / DoS)
- Post-run audit log: what files were touched, what network connections were made, what processes were spawned
- `kinnoo run --dry-run` mode that traces what the agent *would* do without allowing side effects

**Files**: [src/kinnoo/run_command.py](src/kinnoo/run_command.py), new `src/kinnoo/runtime_monitor.py`

---

### Summary: The Security Value Proposition

| Threat | Raw OpenClaw | kinnoo + OpenClaw |
|---|---|---|
| Malicious npm packages | `npm install` runs arbitrary lifecycle scripts | Lifecycle script detection + `--ignore-scripts` + `npm audit` gate |
| Hardcoded credentials in agent | User must manually read all code | Automated sweep of JS/TS/JSON for credential patterns |
| Unknown permission requirements | Agent gets full host access by default | Declared permissions + install-time consent + runtime sandboxing |
| Tampered distribution | No signing; TOFU at best | Ed25519 archive signatures + publisher verification |
| Runtime misbehavior | No monitoring post-launch | Syscall monitoring, permission enforcement, resource limits, kill switch |
| Credential exfiltration via memory/ | Memory shipped as-is | Memory contents scanned for credential patterns before pack |

**The pitch**: "kinnoo is the safe way to install and run third-party AI agents - including OpenClaw agents - with the same verification, sandboxing, and monitoring you expect from any package manager."

---

Want me to persist this analysis to the notes file, or refine any of these feature proposals?


## Parallel Conversation with Gemini model about OpenClaw support in kinnoo (using Agnt as proxy name in that conversation)

Implementing support for **OpenClaw** (the "Linux of Agents") into your **Agnt** platform is a high-impact move. In 2026, OpenClaw has become the standard for "personal" automation, and by bridging it to Agnt, you provide the professional-grade security and distribution it currently lacks.

Here is the technical blueprint for the **Agnt x OpenClaw** integration.

---

### ## 1. Scaffolding: `agnt init --template openclaw`
To support scaffolding, Agnt shouldn't reinvent the wheel. It should act as a wrapper around the native OpenClaw setup while injecting your own manifest.

* **The Command:** `agnt init --framework openclaw`
* **What it does:**
    1.  Calls `openclaw setup --workspace ./workspace --non-interactive` to create the standard folder structure.
    2.  Generates the core identity files: `SOUL.md`, `USER.md`, and `AGENTS.md`.
    3.  Creates an `agnt.yaml` that points to these files.

### ## 2. Running: The "NodeJS Sidecar" Runtime
Since OpenClaw is a Node.js process (v22+), your Python-based Agnt platform needs to manage a **Node.js Environment**.

* **Runtime Logic:** When `agnt run` detects an OpenClaw agent, it:
    1.  Checks for `node` and `openclaw` globally or in a local `.agnt/bin`.
    2.  Launches the **Gateway process** using `subprocess.Popen(["openclaw", "gateway", "--port", "18789"])`.
    3.  Provides a **"Terminal Surface"**: In your interactive mode, Agnt routes your terminal input directly to the OpenClaw session via a WebSocket or the `openclaw message send` CLI.

### ## 3. The "Agnt-ify" Import Logic
Converting an existing OpenClaw agent into an Agnt-compatible one is essentially a **Manifest Generation** task.

* **The `agnt import` logic:**
    * **Scan:** Look for an `openclaw.json` or a `SOUL.md` file.
    * **Parse:** Read `openclaw.json` to find which **Skills** (tools) and **Channels** (WhatsApp/Slack) are enabled.
    * **Map:** Convert the OpenClaw configuration into the Agnt manifest format.
    * **Move:** Relocate the `workspace/` files into a standard Agnt structure.

### ## 4. Updated `agnt.yaml` for OpenClaw Support
You need specific fields to handle OpenClaw's unique "Identity-first" architecture.

```yaml
# agnt.yaml (OpenClaw Support)
name: "my-personal-assistant"
runtime: "nodejs"
framework: "openclaw"

# Entrypoint for OpenClaw is always the Gateway or a specific Agent ID
entrypoint: "gateway" 

configuration:
  workspace_path: "./workspace"
  identity_files:
    soul: "./workspace/SOUL.md"
    agents: "./workspace/AGENTS.md"
    user: "./workspace/USER.md"

# OpenClaw handles its own tools via "Skills"
tools:
  provider: "openclaw-skills"
  path: "./workspace/skills"
```

### ## 5. Packing & Memory as an Asset
In the `.agnt` package (your distribution format), the **`memory/` folder** must be treated as a "Live Asset."

* **Asset Bundling:** When you run `agnt pack`, the platform should:
    1.  Zip the code and configuration.
    2.  **Snapshot the Memory:** Include the `MEMORY.md` file but *optionally* exclude the daily logs (`memory/YYYY-MM-DD.md`) to keep the package light and private.
* **The "Cold Start" Memory:** When a user pulls a packaged OpenClaw agent, Agnt ensures the `memory/` folder is initialized so the agent "wakes up" with its pre-baked knowledge.

### ## 6. The "Missing Link": What else does Agnt need?
To truly support OpenClaw at a "pro" level, Agnt needs three specific infrastructure additions:

1.  **Dependency Manager (npm/pnpm):** Since OpenClaw skills often require Node packages, your platform must run `npm install` inside the agent's sandbox before the first execution.
2.  **The "Channel Proxy":** OpenClaw wants to talk to Telegram/WhatsApp. Agnt should provide a **Secret Proxy** so that the agent can connect to these services using keys stored in the Agnt Vault, never exposing them to the agent's raw code.
3.  **Automatic "Doctor" Checks:** OpenClaw is prone to environment errors. Agnt should run `openclaw doctor --json` as a "Pre-flight check" before every `agnt run` to ensure the Node environment is healthy.

---

### ## Implementation Summary

| Feature | Difficulty | Agnt Value-Add |
| :--- | :--- | :--- |
| **Scaffolding** | Low | Standardizes the "Chaos" of raw OpenClaw setups. |
| **Running** | Medium | Provides a **Secure Sandbox** (WASM/Container) for Node. |
| **Importing** | Low | Massively grows your registry by absorbing existing agents. |
| **Memory Assets** | Medium | Makes "Trained" memories portable between users. |

**Would you like me to draft the Python code for the `agnt import` script that specifically parses an `openclaw.json` and outputs a valid `agnt.yaml`?**

---

## Follow-up question

**Prompt** What is a "full gateway installation" in OpenClaw and what would it take to support this?

**Response**
In the OpenClaw ecosystem (formerly Clawdbot/Moltbot), a **"Full Gateway Installation"** is the leap from running a simple "one-off" agent script to deploying a **persistent, always-on AI infrastructure.**

While a basic installation might just let you run `openclaw run "do something"`, a **Full Gateway** setup transforms your machine into a central server that stays awake 24/7 to manage messaging channels, scheduled tasks, and remote device connections.

---

### ## 1. What is the Gateway under the hood?
The Gateway is a **Node.js daemon** (background service) that acts as the "Central Nervous System" for all agent activity. It typically runs on port **18789** and performs three critical roles:

* **The Router:** It connects to WhatsApp, Telegram, Discord, and Slack simultaneously. When a message arrives, the Gateway decides which agent "brain" (session) should handle it.
* **The Scheduler (Cron):** It handles the background "heartbeats." If you have an agent that needs to "Scan the news at 8 AM," the Gateway is the process that wakes it up.
* **The WebSocket Hub:** Every client—whether it's the Web UI, the CLI, or a mobile "Node" (your iPhone camera)—connects to this single WebSocket server to talk to the AI.

---

### ## 2. Requirements for a Full Gateway Install
To support this in your **Agnt** platform, you are essentially moving from "Agent Hosting" to **"Server Orchestration."**

| Requirement | What it is | Why it's a challenge for Agnt |
| :--- | :--- | :--- |
| **Persistence** | Uses `systemd` (Linux) or `launchd` (Mac) to survive reboots. | `agnt run` is usually ephemeral; you'll need `agnt start --daemon`. |
| **Port Mapping** | Needs port 18789 open for the Control UI and API. | You’ll need to manage local port conflicts and firewall rules. |
| **Secret Vault** | Stores session tokens for WhatsApp/Telegram. | These aren't just strings; they are complex session blobs that must be encrypted. |
| **Daemonization** | The process must run disconnected from the terminal. | You need a way to "attach" and "detach" your UI from the running background process. |

---

### ## 3. What would it take for Agnt to support this?
If you want to allow users to deploy a "Full OpenClaw Gateway" via Agnt, your platform needs to add these three infrastructure features:

#### **A. The Service Manager (V3 Feature)**
Instead of just executing a script, Agnt must be able to **supervise** a process.
* **Agnt Logic:** `agnt run --service`
* **Function:** Agnt launches the Node.js process, captures its logs to a file, and automatically restarts it if it crashes.

#### **B. The "Channel Onboarding" UI**
A full gateway is useless without a communication channel. To support this, Agnt needs to handle **QR Code rendering**. 
* **The Flow:** When a user runs the gateway, OpenClaw generates a WhatsApp pairing QR code. Agnt must be able to "catch" this from the logs and display it in the terminal or a web view so the user can scan it.

#### **C. Ingress / Remote Access**
Because the Gateway is "always-on," users will want to access it from their phones.
* **The Agnt Solution:** You could integrate a **Tailscale** or **Cloudflare Tunnel** "sidecar." When a user launches a Gateway, Agnt automatically creates a private, secure URL (e.g., `my-agent.agnt.link`) so they can access the Web UI from anywhere.

---

### ## 4. Updated `agnt.yaml` for a Gateway
To support a full installation, your manifest needs to define the **Networking** and **Service** parameters.

```yaml
# agnt.yaml (Gateway Support)
name: "personal-hq"
type: "gateway" # Distinguishes it from a one-shot agent
runtime: "nodejs"

service:
  auto_restart: true
  port: 18789
  health_check: "/api/health"

channels:
  - type: "whatsapp"
    persist_session: true
  - type: "telegram"
    token_env: "TELEGRAM_BOT_TOKEN"

# Gateway needs broader filesystem access than a simple agent
security:
  isolation: "container"
  filesystem:
    workspace: "./workspace"
```

---

### ## The Verdict: Should you do it?
Supporting a "Full Gateway" is a **massive value-add** but a **major engineering lift.**
* **The Reward:** You become the go-to platform for "Personal AI Servers" (the home automation and "AI Twin" crowd).
* **The Risk:** You are now responsible for **uptime**. If the gateway crashes, the user's "AI Employee" stops working.

**I recommend starting with "Single Agent" support first.** Once your sandbox is bulletproof, you can introduce the "Service" layer to handle the 24/7 Gateway requirements.

**Would you like me to show you how the "Process Supervisor" logic would look in Python so you can start planning the `agnt run --service` feature?**


## Final Thoughts and Feature Set for Phase 4 (V4)

Good. I've reviewed both analyses in detail. Here's my reasoning on each of Gemini's suggestions, followed by the consolidated V4 feature set.

---

## Gemini Suggestion Assessment

**Already covered by features 31-41 (no action needed):**
- Scaffolding via `init --framework openclaw` → feature34
- Node.js runtime management → feature31
- Import logic (scan openclaw.json, SOUL.md) → feature36
- Manifest extensions → feature33
- npm/pnpm dependency handling → feature31
- Memory as asset → feature35

**Good ideas to incorporate as enhancements to existing features:**

1. **Node.js environment preflight checks** (Gemini's "Doctor Checks") — Run `node --version` (≥22), check npm/pnpm availability before `kinnoo run` or `kinnoo install`. Kinnoo already has run preflight in Python; this extends it to Node.js. → **Fold into feature31**

2. **Selective state directory packing** (Gemini's "Snapshot the Memory" — exclude daily logs `memory/YYYY-MM-DD.md`, keep core `MEMORY.md`) — Add exclude patterns to `state_dirs` so publishers can control what gets packed. Prevents shipping private daily logs while keeping the "cold start" knowledge base. → **Fold into feature35**

3. **Daemon attach/detach + log streaming** (Gemini's "Terminal Surface") — If we support daemons, users need `kinnoo attach <agent>` for interactive session and `kinnoo logs <agent>` for log tailing. Without these, daemon support is half-baked. → **Fold into feature32**

4. **Identity file detection in import** (Gemini's SOUL.md/USER.md/AGENTS.md signals) — These are strong OpenClaw-specific detection signals. SOUL.md is as strong as openclaw.json for identifying an OpenClaw project. → **Fold into feature36**

**Not V4 scope (deferred):**
- **Channel Proxy / Secret Vault** — gateway-level infrastructure; aligns with the future gateway-bridge concept, not standalone agents
- **Channel Onboarding UI** (QR code rendering) — full gateway concern
- **Ingress / Remote Access** (Tailscale/Cloudflare tunnel) — infrastructure orchestration, not a package manager's job
- **Full Gateway lifecycle management** — we already agreed to defer this

---

## V4 Final Feature Set: JS/TS Runtime & Security Hardening

### Core Runtime (features 31-33)

**feature31: Node.js Runtime Support** *(Foundation — blocks all others)*
- Add `"nodejs"` as runtime language in schema alongside `"python"`
- Entrypoint contract: `node <entrypoint> "<input>"`
- npm/pnpm install during `kinnoo install` (equivalent to pip/venv for Python)
- Exclude `node_modules` from `.kno` archives; include `package.json` + lockfile for reproducibility
- **Node.js preflight checks**: verify `node` ≥22, `npm`/`pnpm` available before run/install (extends existing Python preflight pattern)
- Files: schema.py, run_command.py, install_command.py, pack_command.py, validator.py, analyzer.py

**feature32: Daemon/Long-running Process Support** *(depends on 31)*
- Add `"daemon"` runtime type (alongside `"one-shot"`, `"mcp-server"`)
- `kinnoo run` starts persistent process with PID tracking; `kinnoo stop` sends SIGTERM
- **`kinnoo attach <agent>`** for interactive session with a running daemon (routes stdin/stdout)
- **`kinnoo logs <agent>`** for live log streaming from daemon process
- Reuses existing supervisor.py and health_check.py; works for both Python and Node.js daemons
- Files: schema.py, run_command.py, cli.py, supervisor.py

**feature33: OpenClaw Manifest Extensions** *(depends on 31)*
- Extend kinnoo.yaml: `runtime.package_manager` (npm/pnpm), `channels` (declared integrations), `skills` (SKILL.md paths), `state_dirs` (mutable folders)
- `framework: openclaw` triggers OpenClaw-specific validation rules
- Framework-agnostic schema that also supports future JS/TS frameworks
- Files: schema.py, validator.py, docs/manifest-schema-reference.md

### OpenClaw-Specific (features 34-36)

**feature34: OpenClaw Agent Scaffold Template** *(depends on 31, 33)*
- `kinnoo init my-agent --framework openclaw` generates: `package.json`, `index.mjs`, `openclaw.json`, `skills/default/SKILL.md`, `memory/`, `AGENTS.md`, `SOUL.md`
- Generated from kinnoo's own templates (no openclaw CLI dependency at scaffold time)
- Runnable with `kinnoo run my-agent/ "hello"` after setting API keys
- Files: templates.py, init_command.py

**feature35: Mutable State Folders (memory/) in Pack/Install** *(no dependencies — parallel with 32)*
- New `state_dirs` manifest field for mutable directories (distinct from immutable `assets`)
- Pack captures current state as snapshot; install restores (warns if exists, `--force` to overwrite)
- **Exclude patterns**: `state_dirs[].exclude` for selective packing (e.g., exclude daily logs `memory/YYYY-MM-DD.md`, keep core `MEMORY.md`) — prevents shipping private data while preserving "cold start" knowledge
- Framework-agnostic — useful for any agent, not just OpenClaw
- Files: schema.py, pack_command.py, install_command.py, validator.py

**feature36: OpenClaw Agent Import Support** *(depends on 31, 33, 35)*
- `kinnoo import` detects existing OpenClaw projects via: `package.json` with openclaw dep (high), `openclaw.json` (high), **`SOUL.md`** (high), `SKILL.md` files (medium), `AGENTS.md`/`USER.md` (medium), `memory/` dir (state_dirs candidate)
- Generates complete kinnoo.yaml wrapping existing structure
- Files: analyzer.py, import_command.py

### Security Hardening (features 37-41)

**feature37: Node.js Dependency Audit on Install** *(depends on 31)*
- Run `npm audit` during `kinnoo install`; surface CVE counts
- Block install on critical CVEs (`--allow-vulnerable` to override)
- Detect and warn about lifecycle scripts (`preinstall`/`postinstall`); offer `--ignore-scripts`
- Log dependency tree for reproducibility auditing
- Files: install_command.py

**feature38: Static Analysis Security Sweep for Node.js** *(depends on 31)*
- Extend code_sweep.py to scan `.js`/`.mjs`/`.ts`/`.json` for hardcoded secrets
- Detect dangerous Node.js patterns: `child_process.exec()`, `eval()`, `Function()` constructor, sensitive `fs` operations
- Flag dangerous `openclaw.json` config keys (`dangerously*`, `tools.exec.security: "off"`)
- Scan `memory/` contents for credential patterns before packing
- Files: code_sweep.py

**feature39: Permission Declaration & Runtime Sandboxing** *(no dependencies — benefits all agents)*
- New `permissions` field in kinnoo.yaml: `network`, `filesystem`, `shell`, `browser`, `env_access`
- Install-time permission summary and explicit consent prompt
- `kinnoo run --sandbox` enforces declared permissions (Docker/firejail)
- Files: schema.py, validator.py, run_command.py, install_command.py

**feature40: Archive Signing & Publisher Verification** *(no dependencies — benefits all agents)*
- `kinnoo pack --sign` signs with Ed25519 private key
- `kinnoo install` verifies against publisher's registered public key
- `kinnoo keygen` for keypair generation
- Unsigned archives get "UNVERIFIED PUBLISHER" warning
- Files: new signing.py, pack_command.py, install_command.py

**feature41: Runtime Behavior Monitoring & Kill Switch** *(depends on 39)*
- Monitor subprocess: network connections, file writes outside workspace, process spawning
- Auto-kill on permission violation; resource limits (CPU, memory, wall-clock)
- Post-run audit log
- `kinnoo run --dry-run` traces actions without side effects
- Files: run_command.py, new runtime_monitor.py

---

### Dependency Graph

```
feature31 (Node.js Runtime) ───┬── feature32 (Daemon + attach/logs)
                                ├── feature33 (Manifest Ext.) ──┬── feature34 (Scaffold)
                                │                                └── feature36 (Import) ←── feature35
                                ├── feature37 (npm Audit)
                                └── feature38 (JS Security Sweep)

feature35 (State Folders)  ────── parallel, no deps ───────────── feature36 (Import)

feature39 (Permissions)    ────── no deps (all agents) ────────── feature41 (Runtime Monitor)
feature40 (Signing)        ────── no deps (all agents)
```

### Implementation Order (4 waves)

1. **Wave 1**: feature31 (Node.js Runtime) + feature35 (State Folders) + feature39 (Permissions) + feature40 (Signing) — *all independent foundations*
2. **Wave 2**: feature32 (Daemon) + feature33 (Manifest Ext.) + feature37 (npm Audit) + feature38 (JS Sweep) — *depend on wave 1*
3. **Wave 3**: feature34 (Scaffold) + feature36 (Import) + feature41 (Runtime Monitor) — *depend on wave 2*
4. **Deferred**: Gateway-bridge (register as OpenClaw skill) — *after V4*

---

### What was excluded from V4 (and why)
- **Full gateway lifecycle** — kinnoo is a package manager, not a server orchestrator
- **Channel proxy / secret vault** — gateway-level infrastructure
- **Channel onboarding UI** — gateway concern
- **Ingress/remote access** — infrastructure, not packaging
- **TypeScript entrypoints (.ts)** — start with .mjs/.js; TS compilation support deferred

---

Want me to refine any of these, or shall we proceed to writing them into FEATURES.txt?