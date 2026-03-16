"""Project analyzer library for inferring manifest-relevant fields.

Feature27 task158 establishes a stable analyzer API and report contract.
Detector implementations are intentionally conservative at this stage and can
be extended by follow-up tasks without breaking API shape.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
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
    imports = _collect_import_names(project_dir)

    framework_patterns: dict[str, tuple[str, ...]] = {
        "gemini": ("google.genai", "google.generativeai"),
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

    if len(matched) == 1:
        return DetectorResult(
            value=matched[0],
            confidence=0.85,
            evidence=f"Framework signals detected -> {evidence_details[0]}.",
            warning=None,
        )

    if len(matched) > 1:
        return DetectorResult(
            value=None,
            confidence=0.3,
            evidence=f"Multiple framework signals detected: {'; '.join(evidence_details)}.",
            warning="Framework inference is ambiguous; multiple framework indicators were found.",
        )

    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence="No known framework import patterns detected.",
        warning="Could not infer framework; no recognized framework imports were found.",
    )


def _detect_dependencies(project_dir: Path) -> DetectorResult:
    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence=f"dependency detector not implemented for {project_dir.name}",
        warning="Could not infer dependencies yet; review requirements manually.",
    )


def _detect_env_vars(project_dir: Path) -> DetectorResult:
    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence=f"env-var detector not implemented for {project_dir.name}",
        warning="Could not infer env vars yet; review source for required variables.",
    )


def _detect_assets(project_dir: Path) -> DetectorResult:
    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence=f"asset detector not implemented for {project_dir.name}",
        warning="Could not infer assets yet; review data/model files manually.",
    )


def _detect_services(project_dir: Path) -> DetectorResult:
    return DetectorResult(
        value=[],
        confidence=0.0,
        evidence=f"service detector not implemented for {project_dir.name}",
        warning="Could not infer services yet; review external service dependencies manually.",
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
