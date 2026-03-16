"""Project analyzer library for inferring manifest-relevant fields.

Feature27 task158 establishes a stable analyzer API and report contract.
Detector implementations are intentionally conservative at this stage and can
be extended by follow-up tasks without breaking API shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


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


def _detect_entrypoint(project_dir: Path) -> DetectorResult:
    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence=f"entrypoint detector not implemented for {project_dir.name}",
        warning="Could not infer entrypoint yet; verify project startup script manually.",
    )


def _detect_runtime(project_dir: Path) -> DetectorResult:
    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence=f"runtime detector not implemented for {project_dir.name}",
        warning="Could not infer runtime yet; set runtime fields manually.",
    )


def _detect_framework(project_dir: Path) -> DetectorResult:
    return DetectorResult(
        value=None,
        confidence=0.0,
        evidence=f"framework detector not implemented for {project_dir.name}",
        warning="Could not infer framework yet; set framework explicitly if needed.",
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
