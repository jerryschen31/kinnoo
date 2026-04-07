from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_feature96_group1() -> None:
    readme = ROOT / "README.md"
    supported = ROOT / "docs" / "supported-agents.md"

    readme_text = readme.read_text(encoding="utf-8")
    supported_text = supported.read_text(encoding="utf-8")

    assert "# Kinnoo" in readme_text
    assert "img.shields.io" in readme_text  # badges
    assert "## Installation" in readme_text
    assert "pip install kinnoo" in readme_text
    assert "## Quick Start" in readme_text
    assert "## Documentation" in readme_text
    assert "docs/supported-agents.md" in readme_text

    assert "# Supported Agents" in supported_text


def test_feature96_group2() -> None:
    readme = ROOT / "README.md"
    supported = ROOT / "docs" / "supported-agents.md"

    readme_text = readme.read_text(encoding="utf-8")
    supported_text = supported.read_text(encoding="utf-8")

    # AC4 matrix columns
    for header in ["Init scaffold", "Pack", "Run", "Publish", "Install"]:
        assert header in supported_text

    # AC5 no internal-dev references in README
    forbidden_markers = ["notes/", "scratch/", "TASKS.txt", "TESTS.txt", "FEATURES.txt"]
    for marker in forbidden_markers:
        assert marker not in readme_text