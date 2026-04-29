# Understanding `kinnoo run` Flags and Permissions

---

**Prompt:**

For ```kinnoo run``` what exactly do the following do:
1. --thinking {low,medium,high} for openclaw. And what parameters or flags are passed to openclaw as a passthrough?
2. --sandbox - what exactly does this do and how does this work?
3. --max-cpu-seconds - how is cpu time budget tracked during a kinnoo run. In other words, how does kinnoo run know when the max threshold has been hit?
4. --max-memory-mb - how is memory usage tracked during a kinnoo run, i.e. how does kinnoo run know when the max has been hit?
5. --no-guard - what exactly does this do? What kind of safety checks are typically done on a kinnoo run?

**Response:**

Here's a detailed breakdown of how each `kinnoo run` flag works, based on the code in src/kinnoo/run_command.py:

---

### 1. `--thinking {low,medium,high}` for openclaw

- **Purpose:** When running an agent with `type: openclaw-skill`, this flag sets the "thinking" level for the OpenClaw agent.
- **How it's used:** If provided, `--thinking` is passed as `--thinking <value>` to the delegated `openclaw agent` command.
- **Passthrough parameters:** The following are passed to OpenClaw:
  - `--agent <agent_name>`
  - `--message <input>`
  - `--thinking <low|medium|high>` (if set)
  - `--json` (if `--openclaw-json-output` is set)
  - Any additional passthrough args are appended.
- **Reference:** See the delegated command construction in run_command.py.

---

### 2. `--sandbox`

- **Purpose:** Enforces a runtime policy check before execution.
- **How it works:** Calls `evaluate_sandbox_permissions()` with the manifest and runtime info. If the policy is violated:
  - Depending on enforcement mode, the run is either blocked or allowed with a warning.
  - Violation events are logged and surfaced to the user.
- **Effect:** If the sandbox check fails and enforcement is "terminate", the run is aborted. If "warn", a warning is shown but execution continues.
- **Reference:** See the sandbox logic in run_command.py.

---

### 3. `--max-cpu-seconds`

- **Purpose:** Limits the maximum CPU time (in seconds) the agent process can consume.
- **How it's enforced:** On POSIX systems, this sets a resource limit (`RLIMIT_CPU`) using the `resource` module before launching the subprocess.
- **Tracking:** The OS kernel tracks CPU time; if the process exceeds the limit, it is killed.
- **Reference:** See resource limit setup in _build_posix_resource_preexec.

---

### 4. `--max-memory-mb`

- **Purpose:** Limits the maximum resident set size (memory, in MB) for the agent process.
- **How it's enforced:** On POSIX systems, sets `RLIMIT_AS` (address space) using the `resource` module.
- **Tracking:** The OS kernel enforces this; exceeding the limit kills the process.
- **Reference:** See memory limit logic in _build_posix_resource_preexec.

---

### 5. `--no-guard`

- **Purpose:** Disables input safety checks.
- **How it works:** Normally, kinnoo runs a guard (from `input_guard`) to check for unsafe or suspicious input (e.g., prompt injections, secrets, etc.). With `--no-guard`, these checks are skipped.
- **Safety checks performed (when enabled):**
  - Checks the main input and all passthrough parameters for threats.
  - Warns about suspicious content and asks for confirmation before proceeding.
  - In non-interactive mode, aborts on warnings.
- **Reference:** See guard logic in run_command.py.

---

### Summary Table

| Flag                | Purpose/Effect                                                                 | Enforcement/Mechanism                |
|---------------------|-------------------------------------------------------------------------------|--------------------------------------|
| `--thinking`        | Sets OpenClaw agent "thinking" level; passed to `openclaw agent`              | Delegated as `--thinking`            |
| `--sandbox`         | Enforces runtime policy; blocks or warns on violation                         | Policy check + enforcement           |
| `--max-cpu-seconds` | Sets max CPU time for agent process                                           | OS-level RLIMIT_CPU                  |
| `--max-memory-mb`   | Sets max memory for agent process                                             | OS-level RLIMIT_AS                   |
| `--no-guard`        | Disables input safety checks                                                  | Skips input_guard checks             |

---

If you want to see the exact code for any of these mechanisms, let me know!

---

**Prompt:**

Follow-up questions:
1. So input safety checks are run by default with 'kinnoo run'?
2. Will max-memory-gb and max-cpu-seconds work on most Mac OS X and Linux Operating systems? And what about Windows?
3. What is a permissions policy? Where do I put this policy, and can you give me a few examples?

**Response:**

Here are answers to your follow-up questions:

---

### 1. Are input safety checks run by default with `kinnoo run`?

**Yes.**  
By default, `kinnoo run` performs input safety checks using the input guard. These checks scan the main input and any passthrough parameters for threats (like prompt injections, secrets, or suspicious content).  
- If a warning is detected, you are prompted to confirm before proceeding (unless in non-interactive mode, where the run aborts).
- You can disable these checks with the `--no-guard` flag.

---

### 2. Will `--max-memory-mb` and `--max-cpu-seconds` work on most macOS, Linux, and Windows systems?

- **macOS and Linux:**  
  These flags work on most Unix-like systems, as they use the POSIX `resource` module (`RLIMIT_AS` for memory, `RLIMIT_CPU` for CPU time).  
  - There may be some platform-specific limitations (e.g., containerized environments or certain macOS versions), but generally, they are supported.

- **Windows:**  
  These resource limits **do not work** on Windows. The `resource` module is not available, so the limits are ignored and a warning is printed.

---

### 3. What is a permissions policy? Where do I put this policy, and can you give examples?

**Permissions policy** in kinnoo defines what the agent is allowed to do at runtime (e.g., network access, file system scope, shell access, browser access).

- **Where to put it:**  
  Permissions are specified in the agent's `kinnoo.yaml` manifest under the `runtime` section, typically as fields like `network`, `filesystem_scope`, `shell`, or `browser`.

- **Examples:**

  **a) Deny all network access:**
  ```yaml
  runtime:
    network: denied
  ```

  **b) Restrict filesystem access to a subdirectory:**
  ```yaml
  runtime:
    filesystem_scope: ./data
  ```

  **c) Allow shell commands:**
  ```yaml
  runtime:
    shell: allowed
  ```

  **d) Deny browser automation:**
  ```yaml
  runtime:
    browser: denied
  ```

- **How it works:**  
  When you run with `--sandbox`, kinnoo checks these policies before execution. If the agent tries to perform an action outside its declared permissions, the run is blocked or warned (depending on enforcement mode).

---

If you want to see a full manifest example or more advanced policy combinations, let me know!

---

**Prompt:**

Yes, give a comprehensive list of policy permissions, so that I can document this. Also, does the kinnoo CLI actually enforce these permissions, or is this just boilerplate code at this point (check codebase) ?

**Response:**

Here’s a comprehensive summary for documentation:

---

## 1. Comprehensive List of Policy Permissions

In `kinnoo.yaml`, permissions are specified under the `permissions` section. The main supported permissions are:

| Permission         | Type    | Values / Example                | Description                                                      |
|--------------------|---------|---------------------------------|------------------------------------------------------------------|
| `network`          | bool    | `true` / `false`                | Allow or deny all network access                                 |
| `shell`            | bool    | `true` / `false`                | Allow or deny shell command execution                            |
| `filesystem_scope` | string  | `"none"`, `"workspace-write"`, `"full"` | Controls write access: none, workspace only, or full system      |
| `browser`          | bool    | `true` / `false`                | Allow or deny browser automation                                 |

**Example:**
```yaml
permissions:
  network: false
  shell: false
  filesystem_scope: workspace-write
  browser: false
```

- `network: true` allows network access; `false` blocks it.
- `shell: true` allows shell execution; `false` blocks it.
- `filesystem_scope: workspace-write` allows writing only within the agent workspace.
- `filesystem_scope: full` allows writing anywhere on the filesystem.
- `filesystem_scope: none` blocks all write access.
- `browser: true` allows browser automation (e.g., Selenium); `false` blocks it.

---

## 2. Does the kinnoo CLI actually enforce these permissions?

**Yes, enforcement is implemented and active when you use `--sandbox`.**

- The CLI checks the `permissions` section in your manifest.
- If you attempt a forbidden action (e.g., network access with `network: false`), the run is blocked or a warning is shown, depending on enforcement mode.
- Enforcement is performed by the `evaluate_sandbox_permissions()` function (see src/kinnoo/sandbox.py), which is called during `kinnoo run --sandbox`.
- If a violation is detected, the run is aborted (or warned, depending on enforcement mode).
- The CLI does not instrument OS syscalls, but infers intent from CLI arguments and manifest configuration.

**Without `--sandbox`, the permissions section is not enforced—it's just documentation.**

---

## 3. Example Manifest Permissions Section

```yaml
permissions:
  network: false
  shell: false
  filesystem_scope: workspace-write
  browser: false
```

**Other valid values:**
```yaml
permissions:
  network: true
  shell: true
  filesystem_scope: full
  browser: true
```

---

## 4. How Enforcement Works

- When you run with `--sandbox`, kinnoo:
  - Reads the `permissions` section.
  - Checks your command-line arguments and manifest for forbidden actions.
  - Aborts or warns if you attempt a forbidden action.
- Example: If you pass a URL as an argument but `network: false`, the run is blocked.

---

**Summary:**  
- Supported permissions: `network`, `shell`, `filesystem_scope`, `browser`.
- Enforcement is real and active with `--sandbox`.
- Without `--sandbox`, permissions are not enforced.

Let me know if you want a ready-to-copy documentation block or more advanced examples!

---

## kinnoo run --json for non-openclaw agents

Great idea! For non-openclaw `kinnoo run --json`, you want a structured JSON output that is useful for automation, logging, and downstream tools. Here are recommended key-value pairs to include:

---

### Recommended JSON Output Structure for `kinnoo run --json`

| Key                | Type      | Description                                                                                   |
|--------------------|-----------|-----------------------------------------------------------------------------------------------|
| `output`           | string or object | The main output from the agent run (raw string, or parsed JSON if agent emits JSON)         |
| `exit_code`        | integer   | The process exit code                                                                         |
| `success`          | boolean   | True if exit_code == 0, else false                                                            |
| `start_time`       | string    | ISO 8601 timestamp when the run started                                                       |
| `end_time`         | string    | ISO 8601 timestamp when the run ended                                                         |
| `duration_seconds` | float     | Total wall-clock duration of the run                                                          |
| `agent_dir`        | string    | Path to the agent directory used                                                              |
| `entrypoint`       | string    | Entrypoint file executed                                                                      |
| `runtime_language` | string    | Runtime language used (e.g., python, javascript, typescript)                                  |
| `runtime_type`     | string    | Runtime type (e.g., one-shot, mcp-server, daemon, openclaw-skill)                             |
| `input`            | string or object | The input provided to the agent (raw string or JSON, if applicable)                         |
| `error`            | string or object | Error message or stack trace if the run failed                                              |
| `warnings`         | array     | Any warnings encountered (e.g., input guard warnings, policy warnings)                        |
| `resource_usage`   | object    | (Optional) Resource usage summary: CPU seconds, max memory MB, etc. (if tracked)              |
| `policy_enforced`  | boolean   | True if sandbox/policy enforcement was active                                                 |
| `policy_violations`| array     | List of any policy violations detected                                                        |
| `stdout`           | string    | (Optional) Raw stdout captured from the agent process                                         |
| `stderr`           | string    | (Optional) Raw stderr captured from the agent process                                         |

---

### Example Output

```json
{
  "output": "42",
  "exit_code": 0,
  "success": true,
  "start_time": "2026-04-10T12:34:56Z",
  "end_time": "2026-04-10T12:34:57Z",
  "duration_seconds": 1.23,
  "agent_dir": "./my-agent",
  "entrypoint": "main.py",
  "runtime_language": "python",
  "runtime_type": "one-shot",
  "input": "What is 6 x 7?",
  "warnings": [],
  "policy_enforced": true,
  "policy_violations": [],
  "resource_usage": {
    "cpu_seconds": 0.8,
    "max_memory_mb": 45
  },
  "stdout": "42\n",
  "stderr": ""
}
```

---

### Notes

- If the agent emits structured JSON, you may want to parse and include it under `output` as an object.
- If the run fails, include `error` and set `success: false`.
- `resource_usage` is optional and only included if tracked.
- `policy_enforced` and `policy_violations` help with auditability.
- `stdout` and `stderr` are useful for debugging, even if `output` is parsed.

---

Let me know if you want a ready-to-copy schema or more details on any field!
