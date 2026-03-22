[todo] analyze the codebase for each of the LangChain agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[todo] analyze the codebase for each of the Open AI agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[todo] analyze the codebase for each of the Pydantic AI agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[todo] analyze the codebase for each of the OpenClaw agents in example-scratch/agents/ - ready code comments, metadata and linked repo for more information - and report out how each of these agents can and should be run, as a section in notes/features/feature46-notes.md. If relevant, give suggestions on how kinnoo run should be modified to accomodate running this agent - e.g., maybe a more dedicated wrapper is needed.

[improvement] analyzer needs to detect the type of inputs an imported agent expects to receive - single text input? No jnput? JSON? parameterized input? What parameters? This info needs to get recorded in kinnoo.yaml in an appropriate field. Same for outputs. 

[thought] should think about adding evals sooner or later. kinnoo run —eval test-runs.evals will do runs against the evals test list and give a report. The eval score gets set in kinnoo.yaml next to version (eval-score: and eval-dataset: ). Consider if running evals should be a flag in kinnoo run, or if a separate eval or test CLI command makes more sense. Or maybe both have their place in the kinnoo CLI. In thinking about evals, consider what we’ve already discussed in our tech lead agent notes and our other planning notes. 

[thought] regarding evals, help me think about how to do “security” evals within kinnoo as a CLI command - how secure an agent is - this includes whether an agent has the potential to expose secrets, how vulnerable an agent is to SQL or other injection, how malicious an agent could be based on its default permissions, etc. Are there good eval test sets out there for doing these types of evals?

[improvement] when running kinnoo pack - maybe have a flag that allows the user to also run a preflight run, and if PASS then add a metadata field in kinnoo.yaml next to the version, indicating if preflight was run and the status (PASS / FAIL). 

[improvement] in the top-level kinnoo help usage, separate the daemon-specific commands into a separate section (attach, stop, logs). 

[improvement] analyzer should try and auto-detect model and put this model metadata in the kinnoo.yaml. Test auto-detect against default Gemini, Claude-chat and chatgpt init templates.

[improvement] since there’s so many init frameworks now, make the help usage a bit cleaner - one framework per line instead of all on one line. Each framework should have a one-liner description. 

[improvement] add a --language flag to kinnoo init for initializing agents written in different languages. Supported languages are python, js / javascript, and ts / typescript. Error on incompatible combinations (e.g., --framework openclaw --language python should error out). Make sure language-only initializations are barebones templates, while valid combinations (language and framework) should create functional templates as intended. 

[improvement] openclaw init scaffold has remnant python files - requirements.txt and run.py - I’m assuming these are not needed since openclaw is JS based?

[improvement] kinnoo import <github-agent-code-url> <import-path> works by downloading the agent code to the specified import-path on the local machine (downloads to current-working-directory/<agent-code-dir>/ by default, if import-path is not specified). Handle the edge case where <import-path> or current-working-directory/<agent-code-dir>/  already exists by erroring out saying the directory in question already exists. If kinnoo cannot clone / download the code, kinnoo should also intelligently error stating that agent code cannot be downloaded / cloned to local machine (missing credentials, or URL not found, etc…).

[improvement] Add a “kinnoo check” <agent-name | GitHub-agent-code-url> that checks if the agent is compatible with kinnoo out-of-the-box. This would involve import check, inspect check, and run preflight check - in one go, with intelligent fail messages so the dev knows what to fix for kinnoo compatibility. If pointing to a code URL, this downloads the agent code to a folder like /tmp/kinnoo-agent-check/<agent-code>/ and does the checks from there.

[improvement] Pretty print with color on import, preflight run, pack, publish, install, and any other commands where the user needs to respond to user prompts or that provides important information to the user (important = provides information that the user needs to execute subsequent commands).

[potential bug] Preflight fails on venv not found, but agent (overrode runtime.path in kinnoo.yaml) creates virtual environment and runs without error.
