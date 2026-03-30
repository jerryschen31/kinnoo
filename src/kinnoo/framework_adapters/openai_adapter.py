from __future__ import annotations

from pathlib import Path

from . import AdapterResult, detect_node_package_manager, read_text_files


OPENAI_PY_MARKERS = (
    "from agents import",
    "import agents",
    "from openai import",
    "import openai",
)

OPENAI_TS_MARKERS = (
    "from 'openai'",
    'from "openai"',
    "@openai/agents",
)


def apply(project_dir: Path, base_report: dict[str, object]) -> AdapterResult:
    del base_report
    python_sources = read_text_files(project_dir, {".py"})
    node_sources = read_text_files(project_dir, {".ts", ".tsx", ".js", ".mjs", ".cjs"})

    py_hits = sum(1 for marker in OPENAI_PY_MARKERS if any(marker in source for source in python_sources))
    node_hits = sum(1 for marker in OPENAI_TS_MARKERS if any(marker in source for source in node_sources))

    if py_hits <= 0 and node_hits <= 0:
        return AdapterResult(
            framework="openai",
            detected=False,
            coverage_score=0.0,
            inferred_overrides={},
            confidence_overrides={},
            warnings=[],
            unresolved_guidance=[
                "OpenAI adapter could not confirm SDK markers; using generic analyzer.",
            ],
        )

    inferred_runtime: dict[str, object]
    runtime_evidence: str
    if node_hits > py_hits:
        inferred_runtime = {
            "language": "nodejs",
            "type": "one-shot",
            "version": ">=20.0.0",
            "package_manager": detect_node_package_manager(project_dir),
        }
        runtime_evidence = "OpenAI adapter selected Node.js runtime from JS/TS SDK markers."
    else:
        inferred_runtime = {
            "language": "python",
            "type": "one-shot",
            "version": ">=3.10",
        }
        runtime_evidence = "OpenAI adapter selected Python runtime from SDK markers."

    inferred_overrides = {
        "framework": "openai-agents",
        "runtime": inferred_runtime,
    }

    confidence_overrides = {
        "framework": {
            "score": 0.94,
            "evidence": (
                "OpenAI adapter markers matched "
                f"(python={py_hits}, node={node_hits})."
            ),
        },
        "runtime": {
            "score": 0.88,
            "evidence": runtime_evidence,
        },
    }

    return AdapterResult(
        framework="openai",
        detected=True,
        coverage_score=min(1.0, 0.55 + 0.15 * (py_hits + node_hits)),
        inferred_overrides=inferred_overrides,
        confidence_overrides=confidence_overrides,
        warnings=[],
        unresolved_guidance=[
            "Confirm OpenAI credentials and tool wiring before first runtime execution.",
        ],
    )
