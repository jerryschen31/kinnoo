"""Project analyzer library for inferring manifest-relevant fields.

Feature27 task158 establishes a stable analyzer API and report contract.
Detector implementations are intentionally conservative at this stage and can
be extended by follow-up tasks without breaking API shape.
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, Callable

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


@dataclass(frozen=True)
class DetectorResult:
    """Single detector output value plus confidence/evidence metadata."""

    value: Any
    confidence: float
    evidence: str
    warning: str | None = None


@dataclass(frozen=True)
class AnalysisReport:
    """Stable analyzer report contract used by import/onboarding workflows."""

    inferred: dict[str, Any]
    confidence: dict[str, dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Return a dictionary representation with stable top-level keys."""
        return {
            "inferred": self.inferred,
            "confidence": self.confidence,
            "warnings": self.warnings,
        }


Detector = Callable[[Path], DetectorResult]


def _iter_python_files(project_dir: Path) -> list[Path]:
    return sorted(path for path in project_dir.rglob("*.py") if path.is_file())


def _relative_path(project_dir: Path, file_path: Path) -> str:
    return file_path.relative_to(project_dir).as_posix()


def _has_main_guard(file_path: Path) -> bool:
    try:
        source = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return False
    return "if __name__ == '__main__':" in source or "if __name__ == \"__main__\":" in source


def _detect_entrypoint(project_dir: Path) -> DetectorResult:
    run_py = project_dir / "run.py"
    if run_py.exists() and run_py.is_file():
        return DetectorResult(
            value="run.py",
            confidence=0.95,
            evidence="Found conventional run.py entrypoint.",
            warning=None,
        )

    python_files = _iter_python_files(project_dir)
    guarded = [path for path in python_files if _has_main_guard(path)]

    if len(guarded) == 1:
        entrypoint = _relative_path(project_dir, guarded[0])
        return DetectorResult(
            value=entrypoint,
            confidence=0.78,
            evidence=f"Found single __main__ guard in {entrypoint}.",
            warning=None,
        )

    if len(guarded) > 1:
        candidates = ", ".join(_relative_path(project_dir, path) for path in guarded)
        return DetectorResult(
            value=None,
            confidence=0.35,
            evidence=f"Multiple __main__ candidates detected: {candidates}.",
            warning="Entrypoint is ambiguous; multiple executable modules were found.",
        )

    if len(python_files) == 1:
        entrypoint = _relative_path(project_dir, python_files[0])
        return DetectorResult(
            value=entrypoint,
            confidence=0.55,
            evidence=f"Only one python file found: {entrypoint}.",
            warning="Entrypoint inferred from single-file layout; verify before import.",
        )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No clear entrypoint candidates found.",
        warning="Could not infer entrypoint; add run.py or a single __main__ module.",
    )


def _detect_python_version_from_pyproject(project_dir: Path) -> str | None:
    pyproject_path = project_dir / "pyproject.toml"
    if tomllib is None or not pyproject_path.exists():
        return None

    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None

    project_table = data.get("project")
    if isinstance(project_table, dict):
        requires_python = project_table.get("requires-python")
        if isinstance(requires_python, str) and requires_python.strip():
            return requires_python.strip()
    return None


def _detect_runtime_port_hint(project_dir: Path) -> int | None:
    port_pattern = re.compile(r"(?im)^\s*(?:runtime_)?port\s*=\s*(\d{2,5})\s*$")
    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        match = port_pattern.search(source)
        if not match:
            continue
        port = int(match.group(1))
        if 1 <= port <= 65535:
            return port
    return None


def _detect_runtime(project_dir: Path) -> DetectorResult:
    python_files = _iter_python_files(project_dir)
    if not python_files:
        return DetectorResult(
            value=None,
            confidence=0.0,
            evidence="No python files detected for runtime inference.",
            warning="Could not infer runtime; no python source files were found.",
        )

    version = _detect_python_version_from_pyproject(project_dir) or ">=3.10"
    port_hint = _detect_runtime_port_hint(project_dir)

    runtime: dict[str, Any] = {
        "language": "python",
        "version": version,
        "type": "one-shot",
    }
    evidence_parts = ["Detected python source files."]

    if _detect_entrypoint(project_dir).confidence < 0.5:
        runtime.pop("type", None)
        evidence_parts.append("Entrypoint confidence is low; omitted runtime.type.")

    if port_hint is not None:
        runtime["port"] = port_hint
        evidence_parts.append(f"Found runtime port hint: {port_hint}.")

    runtime_confidence = 0.82 if "type" in runtime else 0.45
    warning = None
    if "type" not in runtime:
        warning = "Runtime type is uncertain because entrypoint detection is ambiguous."

    return DetectorResult(
        value=runtime,
        confidence=runtime_confidence,
        evidence=" ".join(evidence_parts),
        warning=warning,
    )


def _module_name_for_path(project_dir: Path, file_path: Path) -> str:
    relative = file_path.relative_to(project_dir)
    parts = list(relative.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    return ".".join(part for part in parts if part and part != "__init__")


def _collect_import_names(project_dir: Path) -> set[str]:
    imports: set[str] = set()
    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        module_name = _module_name_for_path(project_dir, python_path)
        if module_name:
            imports.add(module_name)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    return imports


def _detect_framework(project_dir: Path) -> DetectorResult:
    openclaw_signals = _detect_openclaw_weighted_signals(project_dir)
    openclaw_score = openclaw_signals["score"]
    openclaw_evidence = openclaw_signals["evidence"]

    if openclaw_score >= 0.6:
        strong_count = len(openclaw_signals["strong"])
        medium_count = len(openclaw_signals["medium"])
        evidence_line = (
            "OpenClaw weighted detection score "
            f"{openclaw_score:.2f} (strong={strong_count}, medium={medium_count}). "
            f"Evidence: {'; '.join(openclaw_evidence)}"
        )
        return DetectorResult(
            value="openclaw",
            confidence=min(0.98, openclaw_score),
            evidence=evidence_line,
            warning=None,
        )

    imports = _collect_import_names(project_dir)

    framework_patterns: dict[str, tuple[str, ...]] = {
        "gemini": ("google.genai", "google.generativeai"),
        "langchain": (
            "langchain",
            "langchain_core",
            "langchain_classic",
            "langchain_openai",
            "langchain_community",
            "langchain_text_splitters",
            "langchain_experimental",
        ),
        "chatgpt": ("openai",),
        "claude-chat": ("anthropic",),
        "pydantic-ai": ("pydantic_ai",),
        "langgraph": ("langgraph",),
        "openai-agents": ("agents",),
        "mcp-client": ("mcp",),
    }

    matched: list[str] = []
    evidence_details: list[str] = []
    for framework, patterns in framework_patterns.items():
        hit = [name for name in imports if any(name == marker or name.startswith(f"{marker}.") for marker in patterns)]
        if hit:
            matched.append(framework)
            evidence_details.append(f"{framework}: {', '.join(sorted(hit))}")

    # LangChain projects commonly import OpenAI SDK helpers directly. When
    # LangChain signals are present, treat chatgpt signal as secondary.
    if "langchain" in matched and "chatgpt" in matched:
        filtered_details = [detail for detail in evidence_details if not detail.startswith("chatgpt:")]
        openai_evidence = [detail for detail in evidence_details if detail.startswith("chatgpt:")]
        evidence_line = (
            f"Framework signals detected -> {'; '.join(filtered_details)}. "
            f"Also detected OpenAI SDK imports ({'; '.join(openai_evidence)}), "
            "which are treated as supporting evidence for LangChain workflows."
        )
        return DetectorResult(
            value="langchain",
            confidence=0.9,
            evidence=evidence_line,
            warning=None,
        )

    if len(matched) == 1:
        return DetectorResult(
            value=matched[0],
            confidence=0.85,
            evidence=f"Framework signals detected -> {evidence_details[0]}.",
            warning=None,
        )

    if len(matched) > 1:
        evidence_line = f"Multiple framework signals detected: {'; '.join(evidence_details)}."
        if openclaw_score > 0:
            evidence_line += (
                f" OpenClaw weighted score {openclaw_score:.2f}: "
                f"{'; '.join(openclaw_evidence)}."
            )
        return DetectorResult(
            value=None,
            confidence=0.3,
            evidence=evidence_line,
            warning="Framework inference is ambiguous; multiple framework indicators were found.",
        )

    if openclaw_score >= 0.2:
        return DetectorResult(
            value=None,
            confidence=openclaw_score,
            evidence=(
                f"OpenClaw weighted detection score {openclaw_score:.2f} is below inference threshold. "
                f"Evidence: {'; '.join(openclaw_evidence)}"
            ),
            warning=(
                "OpenClaw detection confidence is mixed; add stronger project markers "
                "(for example openclaw.json or package dependency markers) to remove ambiguity."
            ),
        )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No known framework import patterns detected.",
        warning="Could not infer framework; no recognized framework imports were found.",
    )


def _openclaw_dependency_marker_count(project_dir: Path) -> tuple[int, list[str]]:
    package_json_path = project_dir / "package.json"
    if not package_json_path.exists() or not package_json_path.is_file():
        return 0, []

    try:
        package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return 0, []

    markers: list[str] = []
    dependency_sections = [
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ]
    for section_name in dependency_sections:
        section = package_data.get(section_name)
        if not isinstance(section, dict):
            continue

        for package_name in sorted(section.keys()):
            normalized = str(package_name).strip().lower()
            if not normalized:
                continue
            if normalized == "openclaw" or normalized.startswith("@openclaw/") or "openclaw" in normalized:
                markers.append(f"package.json:{section_name}:{package_name}")

    return len(markers), markers


def _openclaw_skills_signal(project_dir: Path) -> tuple[bool, str | None]:
    skills_root = project_dir / "skills"
    if not skills_root.exists() or not skills_root.is_dir():
        return False, None

    skill_markdown_files = sorted(
        path for path in skills_root.rglob("SKILL.md") if path.is_file()
    )
    if not skill_markdown_files:
        return False, None

    first_match = skill_markdown_files[0]
    relative = _relative_path(project_dir, first_match)
    return True, f"skills-structure:{relative}"


def _openclaw_memory_signal(project_dir: Path) -> tuple[bool, str | None]:
    memory_root = project_dir / "memory"
    if not memory_root.exists() or not memory_root.is_dir():
        return False, None

    return True, "memory-directory:memory/"


def _openclaw_identity_signal(project_dir: Path) -> tuple[float, list[str]]:
    """Detect OpenClaw identity artifacts as explicit medium-confidence signals."""
    score = 0.0
    evidence: list[str] = []

    soul_path = project_dir / "SOUL.md"
    agents_path = project_dir / "AGENTS.md"
    user_path = project_dir / "USER.md"

    has_soul = soul_path.exists() and soul_path.is_file()
    has_agents = agents_path.exists() and agents_path.is_file()
    has_user = user_path.exists() and user_path.is_file()

    if has_soul and has_agents:
        score += 0.2
        evidence.extend(["identity-file:SOUL.md", "identity-file:AGENTS.md"])
    elif has_soul:
        score += 0.1
        evidence.append("identity-file:SOUL.md")
    elif has_agents:
        score += 0.1
        evidence.append("identity-file:AGENTS.md")

    # USER.md is optional context and only increases confidence when present.
    if has_user:
        score += 0.05
        evidence.append("identity-file:USER.md")

    return score, evidence


def _detect_openclaw_weighted_signals(project_dir: Path) -> dict[str, Any]:
    """Detect OpenClaw evidence using weighted strong/medium signals.

    Strong signals have higher confidence contribution than medium signals.
    """
    strong_evidence: list[str] = []
    medium_evidence: list[str] = []
    score = 0.0

    openclaw_json = project_dir / "openclaw.json"
    if openclaw_json.exists() and openclaw_json.is_file():
        strong_evidence.append("openclaw.json")
        score += 0.5

    dependency_marker_count, dependency_evidence = _openclaw_dependency_marker_count(project_dir)
    if dependency_marker_count > 0:
        score += 0.4
        strong_evidence.extend(dependency_evidence)

    has_skills_signal, skills_evidence = _openclaw_skills_signal(project_dir)
    if has_skills_signal and skills_evidence:
        score += 0.15
        medium_evidence.append(skills_evidence)

    has_memory_signal, memory_evidence = _openclaw_memory_signal(project_dir)
    if has_memory_signal and memory_evidence:
        score += 0.1
        medium_evidence.append(memory_evidence)

    identity_score, identity_evidence = _openclaw_identity_signal(project_dir)
    if identity_score > 0:
        score += identity_score
        medium_evidence.extend(identity_evidence)

    normalized_score = min(1.0, score)
    evidence = strong_evidence + medium_evidence
    return {
        "score": normalized_score,
        "strong": strong_evidence,
        "medium": medium_evidence,
        "evidence": evidence,
    }


def _detect_node_package_manager(project_dir: Path) -> str:
    if (project_dir / "pnpm-lock.yaml").exists():
        return "pnpm"
    return "npm"


def _infer_openclaw_skill_paths(project_dir: Path) -> list[str]:
    skills_root = project_dir / "skills"
    if not skills_root.exists() or not skills_root.is_dir():
        return []

    inferred_skills = sorted(
        _relative_path(project_dir, path)
        for path in skills_root.rglob("SKILL.md")
        if path.is_file()
    )
    return inferred_skills


def _infer_openclaw_state_dirs(project_dir: Path) -> list[str]:
    candidates: list[str] = []

    memory_root = project_dir / "memory"
    if memory_root.exists() and memory_root.is_dir():
        candidates.append("memory")

    state_root = project_dir / "state"
    if state_root.exists() and state_root.is_dir():
        candidates.append("state")

    return candidates


def infer_openclaw_project_hints(project_dir: str | Path) -> dict[str, Any]:
    """Infer OpenClaw runtime and structure hints for import workflows.

    This helper is intentionally additive and does not alter the stable
    `analyze_project()` report key contract from feature27.
    """
    resolved_project_dir = _validate_project_dir(project_dir)
    signals = _detect_openclaw_weighted_signals(resolved_project_dir)

    package_manager = _detect_node_package_manager(resolved_project_dir)
    skills = _infer_openclaw_skill_paths(resolved_project_dir)
    state_dirs = _infer_openclaw_state_dirs(resolved_project_dir)

    return {
        "confidence": float(signals["score"]),
        "evidence": list(signals["evidence"]),
        "runtime": {
            "language": "nodejs",
            "type": "daemon",
            "package_manager": package_manager,
            "version": ">=20.0.0",
        },
        "skills": skills,
        "state_dirs": state_dirs,
    }


def _normalize_package_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _split_requirement_name_and_constraint(requirement: str) -> tuple[str, str]:
    # Keep parsing intentionally narrow/deterministic: name + optional tail constraints.
    requirement = requirement.strip()
    if not requirement:
        return "", ""

    marker_index = requirement.find(";")
    if marker_index >= 0:
        requirement = requirement[:marker_index].strip()

    # Remove extras from name while keeping version constraint suffix intact.
    match = re.match(r"^([A-Za-z0-9_.-]+)(?:\[[^\]]+\])?(.*)$", requirement)
    if not match:
        return "", ""

    name = _normalize_package_name(match.group(1))
    constraint = match.group(2).strip()
    return name, constraint


def _collect_requirements_dependencies(project_dir: Path) -> tuple[dict[str, set[str]], list[str]]:
    requirements_path = project_dir / "requirements.txt"
    requirements: dict[str, set[str]] = {}
    evidence: list[str] = []

    if not requirements_path.exists():
        return requirements, evidence

    try:
        lines = requirements_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return requirements, evidence

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("-r", "--requirement", "-c", "--constraint", "-e", "--editable")):
            continue
        if "://" in stripped:
            continue

        name, constraint = _split_requirement_name_and_constraint(stripped)
        if not name:
            continue

        requirements.setdefault(name, set()).add(constraint)
        evidence.append(f"requirements.txt:{name}{constraint}")

    return requirements, evidence


def _collect_pyproject_dependencies(project_dir: Path) -> tuple[dict[str, set[str]], list[str]]:
    pyproject_path = project_dir / "pyproject.toml"
    dependencies: dict[str, set[str]] = {}
    evidence: list[str] = []

    if tomllib is None or not pyproject_path.exists():
        return dependencies, evidence

    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return dependencies, evidence

    project_table = data.get("project")
    if not isinstance(project_table, dict):
        return dependencies, evidence

    def add_dep(raw_dep: str, source_label: str) -> None:
        name, constraint = _split_requirement_name_and_constraint(raw_dep)
        if not name:
            return
        dependencies.setdefault(name, set()).add(constraint)
        evidence.append(f"{source_label}:{name}{constraint}")

    for dep in project_table.get("dependencies", []):
        if isinstance(dep, str) and dep.strip():
            add_dep(dep, "pyproject.project.dependencies")

    optional = project_table.get("optional-dependencies")
    if isinstance(optional, dict):
        for group_name, dep_list in optional.items():
            if not isinstance(dep_list, list):
                continue
            for dep in dep_list:
                if isinstance(dep, str) and dep.strip():
                    add_dep(dep, f"pyproject.project.optional-dependencies.{group_name}")

    return dependencies, evidence


def _format_dependency_output(dependency_map: dict[str, set[str]]) -> list[str]:
    formatted: list[str] = []
    for package in sorted(dependency_map.keys()):
        constraints = sorted(constraint for constraint in dependency_map[package] if constraint)
        if constraints:
            formatted.append(f"{package}{constraints[0]}")
        else:
            formatted.append(package)
    return formatted


def _detect_dependencies(project_dir: Path) -> DetectorResult:
    requirements_map, requirements_evidence = _collect_requirements_dependencies(project_dir)
    pyproject_map, pyproject_evidence = _collect_pyproject_dependencies(project_dir)

    merged: dict[str, set[str]] = {}
    for source in (requirements_map, pyproject_map):
        for package, constraints in source.items():
            merged.setdefault(package, set()).update(constraints)

    dependencies = _format_dependency_output(merged)
    evidence_items = requirements_evidence + pyproject_evidence

    if dependencies:
        source_count = int(bool(requirements_evidence)) + int(bool(pyproject_evidence))
        confidence = 0.92 if source_count == 2 else 0.82
        return DetectorResult(
            value=dependencies,
            confidence=confidence,
            evidence=f"Detected {len(dependencies)} dependencies from {source_count} source(s): {'; '.join(evidence_items)}",
            warning=None,
        )

    import_dependency_map = {
        "langchain": "langchain",
        "langchain_core": "langchain-core",
        "langchain_classic": "langchain-classic",
        "langchain_openai": "langchain-openai",
        "langchain_community": "langchain-community",
        "langchain_text_splitters": "langchain-text-splitters",
        "langchain_experimental": "langchain-experimental",
        "langgraph": "langgraph",
        "openai": "openai",
        "anthropic": "anthropic",
        "google.genai": "google-genai",
        "google.generativeai": "google-generativeai",
        "pydantic_ai": "pydantic-ai",
        "mcp": "mcp",
    }

    inferred_from_imports: set[str] = set()
    import_evidence: list[str] = []
    import_names = _collect_import_names(project_dir)
    for import_name in sorted(import_names):
        for module_prefix, package_name in import_dependency_map.items():
            if import_name == module_prefix or import_name.startswith(f"{module_prefix}."):
                inferred_from_imports.add(package_name)
                import_evidence.append(f"imports:{import_name}->{package_name}")
                break

    if inferred_from_imports:
        inferred_list = sorted(inferred_from_imports)
        return DetectorResult(
            value=inferred_list,
            confidence=0.68,
            evidence=(
                "Inferred dependencies from known import namespaces in source files: "
                + "; ".join(import_evidence)
            ),
            warning=(
                "Dependency inference came from source imports; verify pinned versions in requirements.txt."
            ),
        )

    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence="No dependencies found in requirements.txt or pyproject.toml.",
        warning="Could not infer dependencies; review requirements.txt and pyproject.toml.",
    )


def _literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _extract_env_var_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "os" and node.func.attr == "getenv" and node.args:
                    key = _literal_string(node.args[0])
                    if key:
                        names.add(key)

            # Match os.environ.get("VAR")
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and isinstance(node.func.value, ast.Attribute)
                and isinstance(node.func.value.value, ast.Name)
                and node.func.value.value.id == "os"
                and node.func.value.attr == "environ"
                and node.args
            ):
                key = _literal_string(node.args[0])
                if key:
                    names.add(key)

        if isinstance(node, ast.Subscript):
            # Match os.environ["VAR"]
            if (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.value.id == "os"
                and node.value.attr == "environ"
            ):
                key = _literal_string(node.slice)
                if key:
                    names.add(key)

    return names


def _detect_env_vars(project_dir: Path) -> DetectorResult:
    env_names: set[str] = set()
    parsed_files = 0

    for python_path in _iter_python_files(project_dir):
        try:
            source = python_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        parsed_files += 1
        env_names.update(_extract_env_var_names(tree))

    inferred = sorted(name for name in env_names if name)
    if inferred:
        return DetectorResult(
            value=inferred,
            confidence=0.88,
            evidence=f"Detected {len(inferred)} unique env var names across {parsed_files} python file(s).",
            warning=None,
        )

    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence=f"No env var patterns detected across {parsed_files} python file(s).",
        warning="Could not infer env vars from source patterns; verify required environment variables manually.",
    )


def _looks_like_safe_relative_path(value: str) -> bool:
    normalized = value.strip().replace("\\", "/")
    if not normalized:
        return False
    if normalized.startswith(("/", "~")):
        return False
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        return False
    return True


def _candidate_asset_directories(project_dir: Path) -> set[str]:
    candidate_names = {"data", "dataset", "datasets", "model", "models", "assets", "artifacts", "checkpoints"}
    candidates: set[str] = set()

    for path in sorted(project_dir.rglob("*")):
        if not path.is_dir():
            continue
        if path.name.lower() not in candidate_names:
            continue
        candidates.add(_relative_path(project_dir, path))

    return candidates


def _candidate_asset_files(project_dir: Path) -> set[str]:
    asset_suffixes = {
        ".onnx",
        ".pt",
        ".pth",
        ".safetensors",
        ".pkl",
        ".pickle",
        ".joblib",
        ".h5",
        ".npy",
        ".npz",
        ".csv",
        ".parquet",
        ".jsonl",
    }
    candidates: set[str] = set()

    for path in sorted(project_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in asset_suffixes:
            continue
        candidates.add(_relative_path(project_dir, path))

    return candidates


def _collect_string_literals(tree: ast.AST) -> list[str]:
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append(node.value)
    return literals


def _collect_path_literal_assets(project_dir: Path) -> tuple[set[str], list[str]]:
    safe_assets: set[str] = set()
    blocked_candidates: list[str] = []

    for python_path in _iter_python_files(project_dir):
        try:
            tree = ast.parse(python_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for literal in _collect_string_literals(tree):
            if "/" not in literal and "\\" not in literal:
                continue

            normalized = literal.strip().replace("\\", "/")
            if not _looks_like_safe_relative_path(normalized):
                blocked_candidates.append(normalized)
                continue

            candidate_path = (project_dir / normalized).resolve()
            try:
                candidate_path.relative_to(project_dir.resolve())
            except ValueError:
                blocked_candidates.append(normalized)
                continue

            if candidate_path.exists() and (candidate_path.is_file() or candidate_path.is_dir()):
                safe_assets.add(_relative_path(project_dir, candidate_path))

    return safe_assets, sorted(set(blocked_candidates))


def _detect_assets(project_dir: Path) -> DetectorResult:
    dir_candidates = _candidate_asset_directories(project_dir)
    file_candidates = _candidate_asset_files(project_dir)
    literal_candidates, blocked_candidates = _collect_path_literal_assets(project_dir)

    inferred_assets = sorted(dir_candidates | file_candidates | literal_candidates)

    warning_parts: list[str] = []
    if blocked_candidates:
        warning_parts.append(
            "Ignored unsafe asset path candidates: "
            + ", ".join(blocked_candidates[:3])
            + (" ..." if len(blocked_candidates) > 3 else "")
        )

    if inferred_assets:
        evidence = (
            f"Detected {len(inferred_assets)} asset candidate(s) "
            f"from directories={len(dir_candidates)}, files={len(file_candidates)}, literals={len(literal_candidates)}."
        )
        confidence = 0.84 if (dir_candidates and file_candidates) else 0.72
        return DetectorResult(
            value=inferred_assets,
            confidence=confidence,
            evidence=evidence,
            warning=" ".join(warning_parts) if warning_parts else None,
        )

    warning_parts.append("Could not infer assets; review model/data files and manifest include paths manually.")
    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence="No model/data asset candidates detected.",
        warning=" ".join(warning_parts),
    )


def _extract_service_endpoints_from_tree(tree: ast.AST) -> set[str]:
    endpoints: set[str] = set()
    for literal in _collect_string_literals(tree):
        if literal.startswith(("http://", "https://", "redis://", "postgres://", "postgresql://")):
            endpoints.add(literal.strip())
    return endpoints


def _service_type_from_endpoint(endpoint: str) -> str:
    lower = endpoint.lower()
    if lower.startswith("redis://"):
        return "redis"
    if lower.startswith(("postgres://", "postgresql://")):
        return "postgres"
    if lower.startswith(("http://", "https://")):
        return "http"
    return "unknown"


def _health_check_hint(service_type: str, endpoint: str) -> str | None:
    if service_type == "redis":
        return "PING"
    if service_type == "postgres":
        return "SELECT 1"
    if service_type == "http":
        parsed = urlsplit(endpoint)
        if parsed.path in {"/health", "/healthz", "/ready", "/readyz"}:
            return f"GET {parsed.path}"
    return None


def _detect_services(project_dir: Path) -> DetectorResult:
    discovered: dict[tuple[str, str], dict[str, Any]] = {}

    for python_path in _iter_python_files(project_dir):
        try:
            tree = ast.parse(python_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue

        for endpoint in _extract_service_endpoints_from_tree(tree):
            service_type = _service_type_from_endpoint(endpoint)
            if service_type == "unknown":
                continue
            key = (service_type, endpoint)
            service = {
                "type": service_type,
                "endpoint": endpoint,
            }
            hint = _health_check_hint(service_type, endpoint)
            if hint:
                service["health_check_hint"] = hint
            discovered[key] = service

    services = [discovered[key] for key in sorted(discovered.keys())]
    if services:
        with_hints = sum(1 for service in services if "health_check_hint" in service)
        return DetectorResult(
            value=services,
            confidence=0.8 if with_hints else 0.7,
            evidence=f"Detected {len(services)} service endpoint(s); {with_hints} include health-check hints.",
            warning=None,
        )

    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence="No recognizable service endpoint patterns found in source literals.",
        warning="Could not infer services; review external endpoint configuration manually.",
    )


def _detector_registry() -> dict[str, Detector]:
    """Return detector hooks keyed by inferred report field name."""
    return {
        "entrypoint": _detect_entrypoint,
        "runtime": _detect_runtime,
        "framework": _detect_framework,
        "dependencies": _detect_dependencies,
        "env_vars": _detect_env_vars,
        "assets": _detect_assets,
        "services": _detect_services,
    }


def _validate_project_dir(project_dir: str | Path) -> Path:
    resolved = Path(project_dir).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Project directory does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {resolved}")
    return resolved


def analyze_project(project_dir: str | Path) -> AnalysisReport:
    """Analyze a project path and return a stable inference report.

    The analyzer is intentionally side-effect free: no writes, prompts, network,
    or runtime execution. It only returns inference metadata.
    """
    resolved_project_dir = _validate_project_dir(project_dir)

    inferred: dict[str, Any] = {}
    confidence: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []

    for field_name, detector in _detector_registry().items():
        result = detector(resolved_project_dir)
        inferred[field_name] = result.value
        confidence[field_name] = {
            "score": float(result.confidence),
            "evidence": result.evidence,
        }
        if result.warning:
            warnings.append(result.warning)

    return AnalysisReport(inferred=inferred, confidence=confidence, warnings=warnings)
