
"""
Agent scaffolding logic for kinnoo init.
"""
import argparse
import sys
import os
import subprocess
from pathlib import Path
from typing import Optional
from kinnoo.templates import (
    KINNOO_YAML_TEMPLATE, MCP_SERVER_KINNOO_YAML_TEMPLATE, OPENCLAW_KINNOO_YAML_TEMPLATE, RUN_PY_TEMPLATE, REQUIREMENTS_TXT_TEMPLATE, README_MD_TEMPLATE,
    GEMINI_RUN_PY, GEMINI_REQUIREMENTS, GEMINI_README,
    CHATGPT_RUN_PY, CHATGPT_REQUIREMENTS, CHATGPT_README,
    CLAUDE_RUN_PY, CLAUDE_REQUIREMENTS, CLAUDE_README,
    PYDANTIC_AI_RUN_PY, PYDANTIC_AI_REQUIREMENTS, PYDANTIC_AI_README,
    LANGGRAPH_RUN_PY, LANGGRAPH_REQUIREMENTS, LANGGRAPH_README,
    OPENAI_AGENTS_RUN_PY, OPENAI_AGENTS_REQUIREMENTS, OPENAI_AGENTS_README,
    MCP_CLIENT_RUN_PY, MCP_CLIENT_REQUIREMENTS, MCP_CLIENT_README,
    MCP_SERVER_RUN_PY, MCP_SERVER_REQUIREMENTS, MCP_SERVER_README,
    OPENCLAW_PACKAGE_JSON_TEMPLATE,
    OPENCLAW_JSON_TEMPLATE,
    OPENCLAW_INDEX_MJS_TEMPLATE,
    OPENCLAW_DEFAULT_SKILL_TEMPLATE,
    OPENCLAW_AGENTS_MD_TEMPLATE,
    OPENCLAW_SOUL_MD_TEMPLATE,
    OPENCLAW_README_TEMPLATE,
)

try:
    from kinnoo.openclaw_preflight import run_openclaw_preflight_for_command
except ImportError:
    from .openclaw_preflight import run_openclaw_preflight_for_command

SUPPORTED_FRAMEWORKS = [
    "gemini",
    "chatgpt",
    "claude-chat",
    "pydantic-ai",
    "langgraph",
    "openai-agents",
    "mcp-client",
    "mcp-server",
    "openclaw",
]

SUPPORTED_LANGUAGES = [
    "python",
    "js",
    "javascript",
    "ts",
    "typescript",
]

_LANGUAGE_ALIASES = {
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
}

_FRAMEWORK_LANGUAGE_COMPATIBILITY = {
    "gemini": {"python"},
    "chatgpt": {"python"},
    "claude-chat": {"python"},
    "pydantic-ai": {"python"},
    "langgraph": {"python"},
    "openai-agents": {"python"},
    "mcp-client": {"python"},
    "mcp-server": {"python"},
    "openclaw": {"javascript", "typescript"},
}

_JS_RUN_TEMPLATE = """const inputText = process.argv[2] || '';
console.log(`Hello from JS agent. Input: ${inputText}`);
"""

_TS_RUN_TEMPLATE = """const inputText = process.argv[2] ?? '';
console.log(`Hello from TS agent. Input: ${inputText}`);
"""

_NODE_PACKAGE_JSON_TEMPLATE = """{{
    "name": "{name}",
    "version": "0.1.0",
    "private": true,
    "type": "module",
    "scripts": {{
        "start": "node {entrypoint}"
    }}
}}
"""

_NODE_README_TEMPLATE = """# {name}

This is a Kinnoo agent scaffolded with `kinnoo init --language {language_flag}`.

- Edit `{entrypoint}` to implement your agent logic.
- See `kinnoo.yaml` for manifest fields.
"""


def _build_openclaw_wrapper_manifest(name: str) -> str:
    """Build schema-compatible OpenClaw wrapper manifest for delegated workspaces."""
    return (
        f"name: {name}\n"
        "version: 0.1.0\n"
        "description: \"OpenClaw workspace managed via kinnoo wrapper\"\n"
        "author: \"TODO: Add author name\"\n"
        "entrypoint: index.mjs\n"
        "framework: openclaw\n"
        "runtime:\n"
        "  language: nodejs\n"
        "  version: \">=20\"\n"
        "  type: daemon\n"
        "  package_manager: npm\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )

KNOWN_FRAMEWORK_DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash-lite",
    "chatgpt": "gpt-5-nano",
    "claude-chat": "claude-sonnet-4-20250514",
    "pydantic-ai": "openai:gpt-4o-mini",
}

def _normalize_language(language: Optional[str]) -> str | None:
    if language is None:
        return None
    return _LANGUAGE_ALIASES.get(language.lower())


def _build_node_manifest(name: str, *, entrypoint: str, language: str) -> str:
    return (
        f"name: {name}\n"
        "version: 0.1.0\n"
        "description: \"TODO: Add a short agent description\"\n"
        "author: \"TODO: Add author name\"\n"
        f"entrypoint: {entrypoint}\n"
        "runtime:\n"
        f"  language: {language}\n"
        "  version: \">=20\"\n"
        "  type: one-shot\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: text\n"
        "outputs:\n"
        "  type: text\n"
    )


def init_agent(
    name: str,
    target_dir: Path,
    framework: Optional[str] = None,
    language: Optional[str] = None,
):
    if framework == "openclaw":
        # Feature77: OpenClaw init delegates lifecycle registration to OpenClaw CLI.
        # Workspace convention is explicit for deterministic install/import/run flows.
        workspace_dir = Path.home() / ".openclaw" / f"workspace-{name}"
        if workspace_dir.exists():
            raise FileExistsError(f"Directory {workspace_dir} already exists.")

        preflight_result = run_openclaw_preflight_for_command("init")
        if not preflight_result.ok:
            raise ValueError(preflight_result.message)

        result = subprocess.run(
            ["openclaw", "agents", "add", name, "--workspace", str(workspace_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            suffix = f" ({detail})" if detail else ""
            raise ValueError(
                "OpenClaw agent registration failed: "
                "`openclaw agents add` returned non-zero exit code"
                f"{suffix}"
            )

        workspace_dir.mkdir(parents=True, exist_ok=True)
        (workspace_dir / "kinnoo.yaml").write_text(
            _build_openclaw_wrapper_manifest(name),
            encoding="utf-8",
        )

        print("[kinnoo init][openclaw] registration complete")
        print(f"[kinnoo init][openclaw] agent={name}")
        print(f"[kinnoo init][openclaw] workspace={workspace_dir}")
        print("[kinnoo init][openclaw] next: edit SOUL.md and configure your OpenClaw model/auth")
        return
    else:
        agent_dir = target_dir / name
        if agent_dir.exists():
            raise FileExistsError(f"Directory {agent_dir} already exists.")

    normalized_language = _normalize_language(language)
    if language is not None and normalized_language is None:
        raise ValueError(
            "Unsupported language. Supported languages: "
            + ", ".join(SUPPORTED_LANGUAGES)
            + "."
        )

    if framework is not None:
        allowed_languages = _FRAMEWORK_LANGUAGE_COMPATIBILITY.get(framework, {"python"})
        chosen_language = normalized_language or ("javascript" if framework == "openclaw" else "python")
        if chosen_language not in allowed_languages:
            allowed_label = ", ".join(sorted(allowed_languages))
            raise ValueError(
                f"Incompatible --framework/--language combination: {framework} + {chosen_language}. "
                f"Allowed language(s) for {framework}: {allowed_label}."
            )

    effective_language = normalized_language or ("javascript" if framework == "openclaw" else "python")
    entrypoint_name = {
        "python": "run.py",
        "javascript": "run.js",
        "typescript": "run.ts",
    }[effective_language]

    agent_dir.mkdir()
    (agent_dir / "tools").mkdir()
    (agent_dir / "prompts").mkdir()

    # OpenClaw uses a Node.js daemon manifest contract; MCP server uses a dedicated Python mcp-server manifest.
    if framework == "openclaw":
        manifest_content = OPENCLAW_KINNOO_YAML_TEMPLATE.format(name=name)
    elif framework == "mcp-server":
        manifest_content = MCP_SERVER_KINNOO_YAML_TEMPLATE.format(name=name)
    elif effective_language in {"javascript", "typescript"}:
        manifest_content = _build_node_manifest(
            name,
            entrypoint=entrypoint_name,
            language=effective_language,
        )
    else:
        manifest_content = KINNOO_YAML_TEMPLATE.format(name=name)

    if framework is not None and framework not in {"openclaw", "mcp-server"}:
        manifest_content += f"framework: {framework}\n"
        default_model = KNOWN_FRAMEWORK_DEFAULT_MODELS.get(framework)
        if default_model is not None:
            manifest_content += f"model: {default_model}\n"

    framework_templates = {
        "gemini": (GEMINI_RUN_PY, GEMINI_REQUIREMENTS, GEMINI_README),
        "chatgpt": (CHATGPT_RUN_PY, CHATGPT_REQUIREMENTS, CHATGPT_README),
        "claude-chat": (CLAUDE_RUN_PY, CLAUDE_REQUIREMENTS, CLAUDE_README),
        "pydantic-ai": (PYDANTIC_AI_RUN_PY, PYDANTIC_AI_REQUIREMENTS, PYDANTIC_AI_README),
        "langgraph": (LANGGRAPH_RUN_PY, LANGGRAPH_REQUIREMENTS, LANGGRAPH_README),
        "openai-agents": (OPENAI_AGENTS_RUN_PY, OPENAI_AGENTS_REQUIREMENTS, OPENAI_AGENTS_README),
        "mcp-client": (MCP_CLIENT_RUN_PY, MCP_CLIENT_REQUIREMENTS, MCP_CLIENT_README),
        "mcp-server": (MCP_SERVER_RUN_PY, MCP_SERVER_REQUIREMENTS, MCP_SERVER_README),
    }

    # Write files
    (agent_dir / "kinnoo.yaml").write_text(manifest_content)
    if framework in framework_templates:
        run_template, requirements_template, readme_template = framework_templates[framework]
        (agent_dir / "run.py").write_text(run_template)
        (agent_dir / "requirements.txt").write_text(requirements_template)
        (agent_dir / "README.md").write_text(readme_template.format(name=name))
    elif effective_language == "javascript":
        (agent_dir / "run.js").write_text(_JS_RUN_TEMPLATE)
        (agent_dir / "package.json").write_text(
            _NODE_PACKAGE_JSON_TEMPLATE.format(name=name, entrypoint="run.js")
        )
        (agent_dir / "requirements.txt").write_text("")
        (agent_dir / "README.md").write_text(
            _NODE_README_TEMPLATE.format(
                name=name,
                language_flag="js",
                entrypoint="run.js",
            )
        )
    elif effective_language == "typescript":
        (agent_dir / "run.ts").write_text(_TS_RUN_TEMPLATE)
        (agent_dir / "package.json").write_text(
            _NODE_PACKAGE_JSON_TEMPLATE.format(name=name, entrypoint="run.ts")
        )
        (agent_dir / "requirements.txt").write_text("")
        (agent_dir / "README.md").write_text(
            _NODE_README_TEMPLATE.format(
                name=name,
                language_flag="ts",
                entrypoint="run.ts",
            )
        )
    elif framework != "openclaw":
        (agent_dir / "run.py").write_text(RUN_PY_TEMPLATE)
        (agent_dir / "requirements.txt").write_text(REQUIREMENTS_TXT_TEMPLATE)
        (agent_dir / "README.md").write_text(README_MD_TEMPLATE.format(name=name))

    if framework == "openclaw":
        # Keep OpenClaw scaffolding deterministic and offline-safe: template writes only, no shell-outs.
        skills_default_dir = agent_dir / "skills" / "default"
        skills_default_dir.mkdir(parents=True)
        (agent_dir / "memory").mkdir()

        (agent_dir / "package.json").write_text(
            OPENCLAW_PACKAGE_JSON_TEMPLATE.format(name=name)
        )
        (agent_dir / "openclaw.json").write_text(
            OPENCLAW_JSON_TEMPLATE.format(name=name)
        )
        (agent_dir / "index.mjs").write_text(OPENCLAW_INDEX_MJS_TEMPLATE)
        (skills_default_dir / "SKILL.md").write_text(OPENCLAW_DEFAULT_SKILL_TEMPLATE)
        (agent_dir / "AGENTS.md").write_text(OPENCLAW_AGENTS_MD_TEMPLATE)
        (agent_dir / "SOUL.md").write_text(OPENCLAW_SOUL_MD_TEMPLATE)
        (agent_dir / "README.md").write_text(OPENCLAW_README_TEMPLATE.format(name=name))

def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new Kinnoo agent directory with manifest and templates."
    )
    parser.add_argument("agent_name", nargs="?", help="Name of the agent directory to create.")
    parser.add_argument("--framework", type=str, default=None, help="Optional framework for agent template.")
    parser.add_argument("--language", type=str, default=None, help="Optional language (python/js/ts) for agent template.")
    args = parser.parse_args()

    # Print usage if agent_name is missing
    if not args.agent_name:
        print("Usage: kinnoo init <agent_name> [--framework <framework>]", file=sys.stderr)
        sys.exit(1)

    framework = args.framework
    if framework is not None:
        fw = framework.lower()
        if fw not in SUPPORTED_FRAMEWORKS:
            print(f"Unsupported framework. The supported frameworks are: {', '.join(SUPPORTED_FRAMEWORKS)}.", file=sys.stderr)
            print("Usage: kinnoo init <agent_name> [--framework <framework>]", file=sys.stderr)
            sys.exit(1)
        framework = fw

    language = args.language
    if language is not None:
        language = language.lower()
        if language not in SUPPORTED_LANGUAGES:
            print(
                f"Unsupported language. Supported languages: {', '.join(SUPPORTED_LANGUAGES)}.",
                file=sys.stderr,
            )
            print(
                "Usage: kinnoo init <agent_name> [--framework <framework>] [--language <language>]",
                file=sys.stderr,
            )
            sys.exit(1)

    # Directory creation and template generation
    try:
        init_agent(args.agent_name, Path(os.getcwd()), framework=framework, language=language)
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
