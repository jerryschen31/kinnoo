# -----------------------
# UAT
# -----------------------

```kinnoo --help``` changes:
1. I want the kinnoo CLI help to show the version number and associated commit hash, and an orange icon 🍊 at the top, with some quick text. So if the current version is 0.7.1 and the associated commit hash for this version is bdc5308, for example, instead of

```
% kinnoo -h
Kinnoo CLI
```

I want to see
```
% kinnoo -h
🍊 Kinnoo CLI v0.7.1 (bdc5308)
```


```kinnoo init``` changes:
1. Remove framework option and instead REQUIRE user to choose a framework as an argument:
usage: kinnoo init [-h] [framework] [--language {python,javascript,typescript}]

Framework argument possibilities stay the same with the addition of “none”: {gemini,chatgpt,claude-chat,pydantic-ai,langgraph,openai-agents,mcp-client,mcp-server,openclaw,no-framework}

Text on no-framework is:no-framework    - Barebones agent template - language should be specified (default: python)

Language text should read “(Optional) Scaffold language (if supported for the specified framework): python, javascript, typescript”

2. ```kinnoo init``` without arguments should launch an interactive wizard:
Step 1: Select framework
Step 2: Select language (If there is an option for the framework).

Supporting languages for each framework:
gemini,chatgpt,claude-chat,langgraph,mcp-client,mcp-server,no-framework : both Python and javascript/ typescript
pydantic-ai,openai-agents : Python-only
openclaw: javascript / typescript

3. openclaw init template needs a very basic MEMORY.md as well (for complete templates - see "Summarizing 5 and 6" section below)

4. change default entrypoint for python-based agents to main.py (not run.py)

5. by default, kinnoo init should create a "complete" template with tools/, prompts/, evals/, tests/, data/ folders and a .gitignore.

6. add a --minimal flag that creates only a minimal agent template (kinnoo.yaml, README.md, entrypoint, requirements file)

Summarizing 5 and 6, we should have:
 - for python-based agent templates (--minimal option): kinnoo.yaml, README.md, requirements.txt, main.py (entrypoint)
 - for python-based agent templates (default complete option): everything in minimal PLUS : prompts/, data/, tools/, tests/, evals/ (all empty folders for the template) and .gitignore
 - for javascript agent templates (not openclaw) (--minimal option): kinnoo.yaml, README.md, package.json, index.js (entrypoint)
 - for javascript agent templates (not openclaw) (default complete option):  everything in minimal PLUS : prompts/, data/, tools/, tests/, evals/ (all empty folders for the template) and .gitignore
 - for typescript agent templates (not openclaw) (--minimal option): kinnoo.yaml, README.md, package.json, index.ts (entrypoint)
 - for typescript agent templates (not openclaw) (default complete option):  everything in minimal PLUS : prompts/, data/, tools/, tests/, evals/ (all empty folders for the template) and .gitignore
 - for openclaw agent templates (--minimal option): kinnoo.yaml, AGENTS.md, IDENTITY.md, SOUL.md, USER.md, README.md
 - for openclaw agent templates (default complete option): everything in minimal PLUS: .gitignore, BOOTSTRAP.md, HEARTBEAT.md, MEMORY.md, skills/, memory/ folders.

7. README.md should (1) correctly specify the entrypoint file to edit for agent run logic, (2) explain that kinnoo.yaml holds the agent manifest, (3) IF a complete agent template is created, explain very briefly (simple two column format) best practices for WHAT kinds of files should go in each folder (tools/, prompts/, evals/, tests/, data/), (4) at the bottom of the README.md file, add a little footer:

---
🍊 *This agent was scaffolded with Kinnoo CLI vX.Y.Z using Schema <kinnoo.yaml version number>.*

8. .gitignore should look like this for python-based agents:

# --- Kinnoo & Agent Ops ---
.kinnoo/             # Local PID files and CLI state
.env                 # API keys
*.pem                # Private keys
.agent-repo-cache*

# --- Git ---
.git/

# --- Environment ---
__pycache__/
.venv/
env/
venv/
*.py[cod]
*$py.class
.pytest_cache/
*.DS_Store*

# --- Data & Distribution ---
dist/
build/
*.egg-info/

9. .gitignore should look like this for javascript-based agents:

# --- Kinnoo & Agent Ops ---
.kinnoo/
.env
*.pem
.agent-repo-cache*

# --- Environment ---
node_modules/
.npm
.pnpm-debug.log*
npm-debug.log*
yarn-debug.log*
yarn-error.log*
*.DS_Store*

# --- Build Artifacts ---
dist/
out/
.cache/

10. .gitignore should look like this for typescript-based agents:

# --- Kinnoo & Agent Ops ---
.kinnoo/
.env
*.pem

# --- Environment ---
node_modules/
.npm
dist/                # Compiled JS output
*.tsbuildinfo        # Incremental build state
.pnpm-debug.log*
npm-debug.log*
yarn-debug.log*
yarn-error.log*
*.DS_Store*
.cache/

# --- Testing & Coverage ---
coverage/
.vitest/

# --- Config & Lockfiles ---
# but ignore local dev overrides
.env.local
.env.development.local

11. .gitignore should look like this for openclaw agents:

--- OpenClaw Core Privacy ---
memory/              # 🛡️ CRITICAL: Ignores all daily YYYY-MM-DD.md logs
.dreams/             # Experimental background consolidation logs
scratch/             # The agent's temporary workspace/download area

# --- Kinnoo & Security ---
.kinnoo/
.env

# --- Credentials & Config ---
.openclaw/           # Local gateway settings & auth tokens
.env
credentials.json
*.pem
*.DS_Store*


```kinnoo pack```
1. kinnoo pack by default should ignore the data/ folder.
2. kinnoo pack should have an option "--include" and "--exclude" that can be flexibly used to include or exclude specific files and folders - e.g., "--include data" can be used to include data.
3. ```kinnoo pack --preflight``` should show WHAT files will be packed and the (estimated) file size of the pack and the destination of the archive, but not actually pack.
4. Pack always writes the checksum sidecar after archive creation (pack_command.py:831) and install verifies the archive against the sidecar before extraction (install_command.py:1421 and install_command.py:1443) BUT in strict mode, missing sidecar is an install error today: install_command.py:1456
5. In the kinnoo pack help usage, the --public flag description should add (without the --public flag, default is private)
6. In the kinnoo pack help usage, the --bump flag description should be: "Increment manifest version before packaging. --bump without a version specified will bump the patch version by default.
7. Implement this functionality: "--bump without a version specified will bump the patch version by default"
8. Since --sign requires --signing-key anyway, I would suggest to remove the --signing-key option and just have the SIGNING_KEY as the argument to --sign. So it would be ```kinnoo pack --sign SIGNING_KEY <my-agent-dir>``` and the help description should say: 
```
Sign packaged archive and emit detached signature artifacts. 
SIGNING_KEY is the path to a Ed25519 private key PEM (new key can be created with 'kinnoo keygen')
```
9. Add a --json flag that returns pack results as a JSON instead of reporting progress and results to stdout. JSON should have key:value pairs for the agent directory, public or private, archive creation file path, checksum sidecar file path, archive size, and agent version, as well as any error codes and messages if the pack errored out.

```kinnoo publish```
1. publish should only allow --local OR --remote, but not both.

2. help usage option should read [--local | --remote] to reflect that only one can be chosen and --local and --remote descriptions should be clear.

3. publish should keep all versions but should show the latest version in the My Agents table or as a table returned with an agent Search. AND to see all versions in the Registry UI, there should be a third tab "Agent Versions" in the modal that appears when a user clicks on an agent name (the other two tabs are "Registry Manifest" and "Agent Manifest"). The "Agent Versions" should show a list of all of the versions along with other relevant info (at this point, not sure what info should be shown other than maybe date uploaded?).

4. Add a --json flag that returns publish results as a JSON instead of reporting progress and results to stdout. JSON should have key:value pairs for the published agent name, published agent version, published registry (remote or local), source archive file path, and remote publish result (accepted or rejected), and any error codes and messages if the publish errored.

```kinnoo install```
1. some of the options and the help menu are deprecated in relation to Openclaw install. With the release of Openclaw 2026.3.28, kinnoo supports Openclaw packing, publishing, installing and running of Openclaw AGENTS, not Openclaw skills themselves - since Openclaw as of at least 2026.3.28 now has the concept of an agent, with the agent files by default saved in ~/.openclaw/workspace-<agent-name>.
2. specifically, these options I think are deprecated, so remove these as options from kinnoo install
  - [--state-overwrite]
  - [--allow-vulnerable] - THIS IS PARTICULAR GOES AGAINST kinnoo's security-first approach
  - [--ignore-scripts]
  - [--openclaw-min-version OPENCLAW_MIN_VERSION]
  - [--openclaw-skill OPENCLAW_SKILL]
3. for openclaw, make sure ```kinnoo install [openclaw-agent]``` defaults to installing the workspace to ~/.openclaw/workspace-<agent-name> BUT with ```kinnoo install [openclaw-agent] [target-dir]``` the user can specify to install the workspace in [target-dir] instead.
4. Add a --json flag that returns publish results as a JSON instead of reporting progress and results to stdout. For now for install, the --json flag can ONLY be used if a non-interactive install (-y) is used. JSON should have key:value pairs for relevant fields and information that are displayed to stdout to the user when a user installs an archive.


```kinnoo run```
1. --json should correctly pass through the --json flag to openclaw agent. For non-openclaw agents, ```kinnoo run --json``` should output a structured JSON output that is useful for automation, logging, and downstream tools. Here are recommended key-value pairs to include:

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

2. Replace --sandbox (confusing) with --enforce-policy (more clear). Sandbox suggests a true isolated sandbox environment, but this flag is really just enforcing the policies specified in kinnoo.yaml.

```kinnoo inspect```
1. Add a --json flag that returns inspect results as a JSON instead of stdout. JSON should have key:value pairs with keys that are named appropriately and show all of the relevant information that stdout shows. JSON should work with --full, --raw, or --update options (adding --skip-warnings should work as well).

2. --update currently expects 3 arguments: agent-target, OLD_KEY, NEW_VALUE. This is a bit unintuitive. Change the behavior of --update to just take 2 arguments: KEY and NEW_VALUE. The --update KEY NEW_VALUE option can come before or after [target], so both ```kinnoo inspect --update runtime.language javascript test-agent-phase13-ts``` and ```kinnoo inspect test-agent-phase13-ts --update runtime.language javascript ``` should work.

3. --update should also warn before actually changing metadata in kinnoo.yaml, and require user to prompt "y" UNLESS --skip-warnings is also present. So if the old value is node.js, for example, ```kinnoo inspect --update runtime.language javascript test-agent-phase13-ts test-agent-phase13-ts``` should show a warning prompt: ```Changing runtime.language from node.js to javascript. Proceed? (y/N):``` with N (no) as default, again unless --skip-warnings is also added.

```kinnoo sync```
Let's comment out this command in the CLI code for now. Make an [agent] comment in the code stating that sync will be implemented later. DO NOT DELETE THE CODE - just comment it out

```kinnoo stop```
Let's comment out this command in the CLI code for now. Make an [agent] comment in the code stating that stop will be implemented later. DO NOT DELETE THE CODE - just comment it out

```kinnoo attach```
Let's comment out this command in the CLI code for now. Make an [agent] comment in the code stating that attach will be implemented later. DO NOT DELETE THE CODE - just comment it out

```kinnoo logs```
Let's comment out this command in the CLI code for now. Make an [agent] comment in the code stating that logs will be implemented later. DO NOT DELETE THE CODE - just comment it out

In the main help menu (kinnoo --help), completely remove the "daemon agents:" section for now by commenting this section out in the code. DO NOT DELETE THE CODE - just comment it out and make an [agent] comment in the code stating that this section will be implemented later.

Registry UI
1. In the My Agents table of agents (and also the agents table shown when Search returns agents), I want to show an additional column "Security" to the right of "Version" column, that holds icons that give security / verifiable information.

I would like the following icons:
✅ (green check): latest agent version is signed, AND the signature has been verified. The signature is verified automatically by the first end-user that installs the agent. When the first end-user of an agent version runs ```kinnoo install``` with --strict mode, kinnoo should send back a request to the server indicating that this agent has been verified. Note that a green check replaces the pen (no need for both).
📦 (box): latest agent version archive integrity / hash has been verified
🧩 (puzzle piece): latest agent version per-file integrity / hash has been verified.
❌ (red x): agent either has an INVALID signature OR did NOT pass archive integrity / hash check OR did NOT pass per-file integrity / hash check. Clicking on the agent name and navigating to the "Security" tab in the modal should give details on what failed (and what passed) - see more on this in point 3 below.

2. Related to this, I would like to run these checks server-side after ANY kinnoo publish of an agent to the remote registry, with these checks then updating that agent's "Security" column with the appropriate icons. Note that these checks should be run server-side in an isolated (containerized) environment. Implement this as three tasks - one task for creating, running and testing the script for doing these checks; one task for updating the "Security" column for that agent in the registry with the appropriate icons as well as writing a short pass/fail report somewhere that can be accessed by the Security tab in the agent modal; and one task for doing and testing all of this within a containerized environment server-side (so the server-side needs to run a quick Lambda function to do this).

3. Clicking on an agent name should show a new tab "Security" in the modal, which should give details on the server-side check runs - what checks were run, which ones passed and which ones failed. Not TOO many details - just one-line per check with a [PASS] or [FAIL] indicated.

# -------------------------------------
# SAT: SWE agent to run
# -------------------------------------
- kinnoo init with all possible options
  - tests should ensure that all possible options create an agent-dir with agent manifest kinnoo.yaml (this makes sure all options actually "work")
  - upon successful init, each type of agent template should include the expected files outlined in the UAT section above (5 and 6 of kinnoo init UAT) AND NOTHING MORE. So, python-based files like requirements.txt should NOT show up for openclaw and JS/TS agents, for example.

- run kinnoo pack with all possible valid options
  - tests should ensure that all possible options exit gracefully
  - tests should ensure that unsupported option combinations should error

- run kinnoo publish with all possible valid options
  - tests should ensure that all possible options exit gracefully
  - tests should ensure that unsupported option combinations should error

- run kinnoo install with all possible wvalid options
  - tests should ensure that all possible options exit gracefully
  - tests should ensure that unsupported option combinations should error



# ---------------------
# Save for later
# ---------------------

- audit trail logs - record when a user uses publish --force to overwrite an existing agent version in the registry. Record Timestamp, Agent name and version, Publisher identity (if available), Requestor IP or authentication info, Old and new archive hashes (if possible).


