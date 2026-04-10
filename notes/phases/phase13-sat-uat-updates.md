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
9. Add a --json flag that returns pack results as a JSON instead of reporting progress and results to stdout. JSON should have key:value pairs for the agent directory, public or private, archive creation file path, checksum sidecar file path, archive size, and agent version.

```kinnoo publish```
1. publish should only allow --local OR --remote, but not both.

2. help usage option should read [--local | --remote] to reflect that only one can be chosen and --local and --remote descriptions should be clear.

3. publish should keep all versions but should show the latest version in the My Agents table or as a table returned with an agent Search. AND to see all versions in the Registry UI, there should be a third tab "Agent Versions" in the modal that appears when a user clicks on an agent name (the other two tabs are "Registry Manifest" and "Agent Manifest"). The "Agent Versions" should show a list of all of the versions along with other relevant info (at this point, not sure what info should be shown other than maybe date uploaded?).


```kinnoo install```
1. some of the options and the help menu are deprecated in relation to Openclaw install. With the release of Openclaw 2026.3.28, kinnoo supports Openclaw packing, publishing, installing and running of Openclaw AGENTS, not Openclaw skills themselves - since Openclaw as of at least 2026.3.28 now has the concept of an agent, with the agent files by default saved in ~/.openclaw/workspace-<agent-name>.
2. specifically, these options I think are deprecated:
  - [--state-overwrite]
  - [--allow-vulnerable] - THIS IS PARTICULAR GOES AGAINST kinnoo's security-first approach
  - [--ignore-scripts]
  - [--openclaw-min-version OPENCLAW_MIN_VERSION]
  - [--openclaw-skill OPENCLAW_SKILL]
3. for openclaw, make sure ```kinnoo install [openclaw-agent]``` defaults to installing the workspace to ~/.openclaw/workspace-<agent-name> BUT with ```kinnoo install [openclaw-agent] [target-dir]``` the user can specify to install the workspace in [target-dir] instead.
4. 


Registry UI
1. In the My Agents table of agents (and also the agents table shown when Search returns agents), show an additional column to the right of version with no column name, that holds icons that indicate if an agent archive is Verified

# -------------------------------------
# SAT: SWE agent to run
# -------------------------------------
- kinnoo init with all possible options
  - tests should ensure that all possible options create an agent-dir with agent manifest kinnoo.yaml (this makes sure all options actually "work")
  - upon successful init, each type of agent template should include the expected files outlined in the UAT section above (5 and 6 of kinnoo init UAT) AND NOTHING MORE. So, python-based files like requirements.txt should NOT show up for openclaw and JS/TS agents, for example.

- run kinnoo pack with all possible valid options
  - tests should ensure that all possible options exit gracefully
  - tests should ensure that unsupported option combinations should error


# ---------------------
# Save for later
# ---------------------

- audit trail logs - record when a user uses publish --force to overwrite an existing agent version in the registry. Record Timestamp, Agent name and version, Publisher identity (if available), Requestor IP or authentication info, Old and new archive hashes (if possible).


