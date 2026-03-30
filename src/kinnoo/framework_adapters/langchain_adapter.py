from __future__ import annotations

from pathlib import Path

from . import AdapterResult, read_text_files


LANGCHAIN_MARKERS = (
    "import langchain",
    "from langchain",
    "import langchain_core",
    "from langchain_core",
)


def apply(project_dir: Path, base_report: dict[str, object]) -> AdapterResult:
    del base_report
    sources = read_text_files(project_dir, {".py"})
    marker_hits = sum(1 for marker in LANGCHAIN_MARKERS if any(marker in source for source in sources))

    if marker_hits <= 0:
        return AdapterResult(
            framework="langchain",
            detected=False,
            coverage_score=0.0,
            inferred_overrides={},
            confidence_overrides={},
            warnings=[],
            unresolved_guidance=[
                "LangChain adapter could not confirm framework markers; using generic analyzer.",
            ],
        )

    inferred_overrides = {
        "framework": "langchain",
        "runtime": {
            "language": "python",
            "type": "one-shot",
            "version": ">=3.10",
        },
    }

    confidence_overrides = {
        "framework": {
            "score": 0.96,
            "evidence": f"LangChain adapter markers matched ({marker_hits} signal(s)).",
        },
        "runtime": {
            "score": 0.9,
            "evidence": "LangChain adapter enforces Python one-shot runtime defaults.",
        },
    }

    return AdapterResult(
        framework="langchain",
        detected=True,
        coverage_score=min(1.0, 0.6 + 0.15 * marker_hits),
        inferred_overrides=inferred_overrides,
        confidence_overrides=confidence_overrides,
        warnings=[],
        unresolved_guidance=[
            "Verify model/provider env vars (for example OPENAI_API_KEY) before first run.",
        ],
    )
