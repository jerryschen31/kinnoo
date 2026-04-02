import subprocess
import sys
import os
import re
import signal
import time
from pathlib import Path
import json

import yaml

from src.kinnoo.registry import RegistryService
from src.kinnoo.registry_backends import MockFilesystemRegistryBackend


CLI_PATH = Path(__file__).resolve().parents[1] / "src" / "kinnoo" / "cli.py"


def test_feature19_import_defaults_to_current_directory(tmp_path):
    project_dir = tmp_path / "feature19-default-path-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import"],
        cwd=project_dir,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Detected values from analyzer:" in result.stdout
    assert "Usage:" not in result.stderr


def test_feature19_import_invalid_args_show_usage(tmp_path):
    project_dir = tmp_path / "feature19-invalid-args-project"
    project_dir.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "extra-arg"],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "usage:" in combined
    assert "import" in combined


def test_feature19_import_writes_manifest_in_place(tmp_path):
    project_dir = tmp_path / "feature19-write-in-place-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello from existing project')\n", encoding="utf-8")
    (project_dir / "notes.txt").write_text("keep me unchanged\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Imported project in-place:" in result.stdout
    manifest_path = project_dir / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "entrypoint: run.py" in manifest_text
    assert "runtime:" in manifest_text
    # Ensure no scaffold-copy behavior: only existing files plus kinnoo.yaml.
    assert not (project_dir / "prompts").exists()
    assert not (project_dir / "tools").exists()
    assert (project_dir / "notes.txt").read_text(encoding="utf-8") == "keep me unchanged\n"


def test_feature19_import_failure_rolls_back_partial_output(tmp_path):
    project_dir = tmp_path / "feature19-rollback-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('rollback project')\n", encoding="utf-8")

    env = dict(os.environ)
    env["KINNOO_IMPORT_FAIL_AFTER_WRITE"] = "1"

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "rolled back partial artifacts" in combined
    assert not (project_dir / "kinnoo.yaml").exists()


def test_feature19_import_collision_requires_explicit_override(tmp_path):
    project_dir = tmp_path / "feature19-collision-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    existing_manifest = (
        "name: existing-agent\n"
        "version: 1.0.0\n"
        "entrypoint: run.py\n"
        "runtime:\n"
        "  type: one-shot\n"
        "  language: python\n"
        "  version: \">=3.10\"\n"
        "dependencies: []\n"
        "inputs:\n"
        "  type: string\n"
        "outputs:\n"
        "  type: string\n"
    )
    manifest_path = project_dir / "kinnoo.yaml"
    manifest_path.write_text(existing_manifest, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    combined = (result.stdout + result.stderr).lower()
    assert "already exists" in combined
    assert "override" in combined
    assert manifest_path.read_text(encoding="utf-8") == existing_manifest

    force_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "--force"],
        input="y\nrun.py\none-shot\n\n",
        capture_output=True,
        text=True,
    )

    assert force_result.returncode == 0
    assert "Imported project in-place:" in force_result.stdout
    assert manifest_path.read_text(encoding="utf-8") != existing_manifest


def test_feature19_import_uses_analyzer_inference_and_warnings(tmp_path):
    project_dir = tmp_path / "feature19-analyzer-integration-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "import anthropic\n"
        "import os\n"
        "token = os.getenv('API_TOKEN')\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\nchatgpt\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = (result.stdout + result.stderr).lower()
    assert "detected values from analyzer" in combined_output
    assert "analyzer warnings" in combined_output
    assert "ambiguous" in combined_output

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "entrypoint: run.py" in manifest_text
    assert "framework: chatgpt" in manifest_text
    assert "requests==2.31.0" in manifest_text
    assert "api_token" in manifest_text.lower()


def test_feature19_confirm_first_wizard_prompt_minimization(tmp_path):
    project_dir = tmp_path / "feature19-confirm-first-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "import openai\n"
        "if __name__ == '__main__':\n"
        "    print('ok')\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("tomli>=2.0\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "Detected values from analyzer:" in combined_output
    assert "Proceed with detected values?" in combined_output
    assert "Provide value for" not in combined_output


def test_feature19_import_keeps_inferred_entrypoint_without_reprompt(tmp_path):
    project_dir = tmp_path / "feature19-inferred-entrypoint-no-reprompt"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "base.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    combined_output = result.stdout + result.stderr
    assert "Detected values from analyzer:" in combined_output
    assert "Proceed with detected values?" in combined_output
    assert "Provide value for entrypoint" not in combined_output

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "entrypoint: base.py" in manifest_text


def test_feature19_conditional_prompts_for_runtime_services_permissions(tmp_path):
    high_confidence_project = tmp_path / "feature19-conditional-prompts-high"
    high_confidence_project.mkdir(parents=True, exist_ok=True)
    (high_confidence_project / "run.py").write_text(
        "import sys\n"
        "import openai\n"
        "service_url = 'https://api.example.com/health'\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )

    high_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(high_confidence_project)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert high_result.returncode == 0
    high_output = high_result.stdout + high_result.stderr
    assert "Provide value for runtime.type" not in high_output
    assert "Provide services" not in high_output
    assert "Configure permissions for mcp-server" not in high_output

    low_confidence_project = tmp_path / "feature19-conditional-prompts-low"
    low_confidence_project.mkdir(parents=True, exist_ok=True)
    (low_confidence_project / "README.md").write_text("no python files yet\n", encoding="utf-8")

    low_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(low_confidence_project)],
        input="y\nrun.py\nmcp-server\n\ny\ny\nn\nn\n/tmp\n",
        capture_output=True,
        text=True,
    )

    assert low_result.returncode == 0
    low_output = low_result.stdout + low_result.stderr
    assert "Provide value for runtime.type" in low_output
    assert "Provide services" not in low_output
    assert "Configure permissions for mcp-server" in low_output

    low_manifest = (low_confidence_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "runtime:" in low_manifest
    assert "type: mcp-server" in low_manifest
    assert "permissions:" in low_manifest


def test_feature19_entrypoint_warning_and_optional_wrapper(tmp_path):
    no_wrapper_project = tmp_path / "feature19-wrapper-default"
    no_wrapper_project.mkdir(parents=True, exist_ok=True)
    (no_wrapper_project / "run.py").write_text(
        "def run():\n"
        "    print('no argv contract')\n",
        encoding="utf-8",
    )

    no_wrapper_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(no_wrapper_project)],
        input="y\n\nn\n",
        capture_output=True,
        text=True,
    )

    assert no_wrapper_result.returncode == 0
    no_wrapper_output = no_wrapper_result.stdout + no_wrapper_result.stderr
    assert "Entrypoint compatibility warning:" in no_wrapper_output
    assert "Generate optional wrapper entrypoint bridge?" in no_wrapper_output
    assert not (no_wrapper_project / "kinnoo_wrapper.py").exists()

    wrapper_project = tmp_path / "feature19-wrapper-opt-in"
    wrapper_project.mkdir(parents=True, exist_ok=True)
    (wrapper_project / "run.py").write_text(
        "def run():\n"
        "    print('no argv contract')\n",
        encoding="utf-8",
    )

    wrapper_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(wrapper_project)],
        input="y\n\ny\n",
        capture_output=True,
        text=True,
    )

    assert wrapper_result.returncode == 0
    wrapper_output = wrapper_result.stdout + wrapper_result.stderr
    assert "Entrypoint compatibility warning:" in wrapper_output
    assert (wrapper_project / "kinnoo_wrapper.py").exists()

    wrapper_manifest = (wrapper_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "entrypoint: kinnoo_wrapper.py" in wrapper_manifest


def test_feature19_interrupt_cleanup_and_exit_code(tmp_path):
    eof_project = tmp_path / "feature19-interrupt-eof"
    eof_project.mkdir(parents=True, exist_ok=True)
    (eof_project / "README.md").write_text("force unresolved prompts\n", encoding="utf-8")

    # Non-interactive EOF should follow defaults for automation-safe behavior.
    eof_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(eof_project)],
        input="",
        capture_output=True,
        text=True,
    )

    assert eof_result.returncode == 0
    assert (eof_project / "kinnoo.yaml").exists()

    sigint_project = tmp_path / "feature19-interrupt-sigint"
    sigint_project.mkdir(parents=True, exist_ok=True)
    (sigint_project / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )

    process = subprocess.Popen(
        [sys.executable, str(CLI_PATH), "import", str(sigint_project)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(0.2)
    if process.poll() is None:
        process.send_signal(signal.SIGINT)
    sigint_stdout, sigint_stderr = process.communicate(timeout=5)

    sigint_output = sigint_stdout + sigint_stderr
    assert process.returncode != 0
    assert "interrupted" in sigint_output.lower()
    assert not (sigint_project / "kinnoo.yaml").exists()
    assert not (sigint_project / "kinnoo_wrapper.py").exists()


def test_feature19_imported_project_runs_in_place(tmp_path):
    project_dir = tmp_path / "feature19-import-runnable"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "requirements.txt").write_text("\n", encoding="utf-8")
    (project_dir / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(f\"imported-runnable:{sys.argv[1] if len(sys.argv) > 1 else ''}\")\n",
        encoding="utf-8",
    )

    import_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )

    assert import_result.returncode == 0
    assert (project_dir / "kinnoo.yaml").exists()

    run_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "run", str(project_dir), "hello-import"],
        capture_output=True,
        text=True,
    )

    combined_output = run_result.stdout + run_result.stderr
    assert run_result.returncode == 0
    assert "imported-runnable:hello-import" in combined_output


def test_feature36_openclaw_detection_weighted_confidence_output(tmp_path):
    strong_project = tmp_path / "feature36-openclaw-import-strong"
    strong_project.mkdir(parents=True, exist_ok=True)
    (strong_project / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (strong_project / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (strong_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-import-strong\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (strong_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (strong_project / "skills" / "default" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (strong_project / "memory").mkdir(parents=True, exist_ok=True)

    strong_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(strong_project)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    strong_output = strong_result.stdout + strong_result.stderr
    assert strong_result.returncode == 0
    assert "framework: openclaw" in strong_output.lower()
    assert "Framework confidence metadata:" in strong_output
    assert "weighted detection score" in strong_output.lower()
    assert "openclaw.json" in strong_output

    medium_project = tmp_path / "feature36-openclaw-import-medium"
    medium_project.mkdir(parents=True, exist_ok=True)
    (medium_project / "run.py").write_text("print('hello')\n", encoding="utf-8")
    (medium_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (medium_project / "skills" / "default" / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (medium_project / "memory").mkdir(parents=True, exist_ok=True)

    medium_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(medium_project)],
        input="y\nopenclaw\n",
        capture_output=True,
        text=True,
    )

    medium_output = medium_result.stdout + medium_result.stderr
    assert medium_result.returncode == 0
    assert "openclaw detection confidence is mixed" in medium_output.lower()
    assert "weighted detection score" in medium_output.lower()


def test_feature36_infers_runtime_skills_state_dirs(tmp_path):
    project_dir = tmp_path / "feature36-openclaw-inference"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (project_dir / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (project_dir / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-openclaw-inference\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (project_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (project_dir / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (project_dir / "skills" / "default" / "SKILL.md").write_text("# Default skill\n", encoding="utf-8")
    (project_dir / "memory" / "daily").mkdir(parents=True, exist_ok=True)
    (project_dir / "memory" / "daily" / "journal.md").write_text("entry\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    manifest_text = (project_dir / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    assert "type: openclaw-skill" in manifest_text
    assert "language: nodejs" in manifest_text
    assert "type: daemon" in manifest_text
    assert "package_manager: pnpm" in manifest_text
    assert "skills:" not in manifest_text
    assert "state_dirs:" not in manifest_text
    assert "channels:" not in manifest_text


def test_feature36_manifest_valid_or_todo_guidance(tmp_path):
    complete_project = tmp_path / "feature36-manifest-guidance-complete"
    complete_project.mkdir(parents=True, exist_ok=True)
    (complete_project / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (complete_project / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (complete_project / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature36-manifest-guidance-complete\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (complete_project / "skills" / "default").mkdir(parents=True, exist_ok=True)
    (complete_project / "skills" / "default" / "SKILL.md").write_text("# Default skill\n", encoding="utf-8")
    (complete_project / "memory").mkdir(parents=True, exist_ok=True)

    complete_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(complete_project)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    complete_output = complete_result.stdout + complete_result.stderr
    assert complete_result.returncode == 0
    assert "Generated manifest validation: PASS" in complete_output

    unresolved_project = tmp_path / "feature36-manifest-guidance-unresolved"
    unresolved_project.mkdir(parents=True, exist_ok=True)
    (unresolved_project / "README.md").write_text("import fixture without executable entrypoint\n", encoding="utf-8")

    unresolved_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(unresolved_project)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )

    unresolved_output = unresolved_result.stdout + unresolved_result.stderr
    assert unresolved_result.returncode == 0
    assert "Generated manifest validation: PASS" in unresolved_output
    assert "TODO guidance:" in unresolved_output
    assert "Verify 'entrypoint' points to an existing executable script in the project root." in unresolved_output
    assert "does not exist in target project" in unresolved_output


def test_feature62_import_openclaw_manifest_migration_guidance(tmp_path):
    project_dir = tmp_path / "feature62-openclaw-import-migration"
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "run.py").write_text(
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    print(sys.argv[1] if len(sys.argv) > 1 else 'ok')\n",
        encoding="utf-8",
    )
    (project_dir / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (project_dir / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature62-openclaw-import-migration\",\n"
        "  \"version\": \"1.0.0\",\n"
        "  \"dependencies\": {\n"
        "    \"@openclaw/core\": \"^0.1.0\"\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (project_dir / "requirements.txt").write_text("\n", encoding="utf-8")

    import_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n",
        capture_output=True,
        text=True,
    )

    assert import_result.returncode == 0, import_result.stdout + import_result.stderr
    manifest_path = project_dir / "kinnoo.yaml"
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    assert "type: openclaw-skill" in manifest_text
    assert "channels:" not in manifest_text
    assert "skills:" not in manifest_text
    assert "state_dirs:" not in manifest_text

    manifest_data = yaml.safe_load(manifest_text)
    manifest_data["provenance"] = {
        "source_registry": "clawhub",
        "source_version": "1.0.0",
    }
    manifest_data["state_dirs"] = ["memory"]
    manifest_path.write_text(yaml.dump(manifest_data), encoding="utf-8")

    inspect_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "inspect", str(project_dir)],
        capture_output=True,
        text=True,
    )

    combined = inspect_result.stdout + inspect_result.stderr
    assert inspect_result.returncode != 0
    assert "provenance" in combined and "source_slug" in combined and "source_url" in combined
    assert "Field 'state_dirs' is not supported in this schema version" in combined


def test_feature64_clawhub_import_scaffold(tmp_path):
    registry_root = tmp_path / "registry"
    service = RegistryService(backend=MockFilesystemRegistryBackend(root=registry_root))
    service.upsert_clawhub_mirror_record(
        agent_slug="weather/weather-skill",
        source_version="2.0.0",
        source_url="https://clawhub.ai/skills/weather/weather-skill",
        synced_at="2026-03-29T04:00:00Z",
        metadata={"description": "Weather skill"},
    )

    destination = tmp_path / "imported-weather-skill"
    env = dict(os.environ)
    env["KINNOO_REGISTRY_ROOT"] = str(registry_root)

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            "--source",
            "clawhub",
            "weather/weather-skill",
            str(destination),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output

    manifest_path = destination / "kinnoo.yaml"
    report_path = destination / "kinnoo-import-report.json"
    assert manifest_path.exists()
    assert report_path.exists()

    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "type: openclaw-skill" in manifest_text
    assert "framework: openclaw" in manifest_text
    assert "source_registry: clawhub" in manifest_text
    assert "source_version: 2.0.0" in manifest_text
    assert "source_slug: weather/weather-skill" in manifest_text

    missing_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            "--source",
            "clawhub",
            "missing/not-found",
            str(tmp_path / "missing-destination"),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    missing_output = missing_result.stdout + missing_result.stderr
    assert missing_result.returncode != 0
    assert "was not found in mirror index" in missing_output
    assert "kinnoo sync clawhub" in missing_output


def test_feature64_clawhub_import_requirements_report(tmp_path):
    registry_root = tmp_path / "registry"
    service = RegistryService(backend=MockFilesystemRegistryBackend(root=registry_root))
    service.upsert_clawhub_mirror_record(
        agent_slug="github/gh-skill",
        source_version="3.1.0",
        source_url="https://clawhub.ai/skills/github/gh-skill",
        synced_at="2026-03-29T05:00:00Z",
        metadata={
            "description": "GitHub helper skill",
            "env_hints": ["GITHUB_TOKEN", "GH_ORG"],
            "config_hints": ["~/.config/gh/config.yml"],
            "bin_hints": ["gh"],
        },
    )

    destination = tmp_path / "imported-gh-skill"
    env = dict(os.environ)
    env["KINNOO_REGISTRY_ROOT"] = str(registry_root)

    result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            "--source",
            "clawhub",
            "github/gh-skill",
            str(destination),
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "Requirement hints:" in output
    assert "env: GH_ORG, GITHUB_TOKEN" in output
    assert "config: ~/.config/gh/config.yml" in output
    assert "bin: gh" in output
    assert "Unresolved guidance:" in output

    report_path = destination / "kinnoo-import-report.json"
    assert report_path.exists()
    report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert report_payload["source"] == "clawhub"
    assert report_payload["slug"] == "github/gh-skill"
    assert report_payload["requirements"]["env"] == ["GH_ORG", "GITHUB_TOKEN"]
    assert report_payload["requirements"]["config"] == ["~/.config/gh/config.yml"]
    assert report_payload["requirements"]["bin"] == ["gh"]
    assert isinstance(report_payload["unresolved"], list) and report_payload["unresolved"]

    inspect_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "inspect", str(destination)],
        capture_output=True,
        text=True,
        env=env,
    )
    inspect_output = inspect_result.stdout + inspect_result.stderr
    assert inspect_result.returncode == 0, inspect_output
    assert "- Provenance:" in inspect_output
    assert "source_registry: clawhub" in inspect_output
    assert "source_slug: github/gh-skill" in inspect_output
    assert "- Imported Requirement Hints:" in inspect_output
    assert "- env: GH_ORG, GITHUB_TOKEN" in inspect_output
    assert "- config: ~/.config/gh/config.yml" in inspect_output
    assert "- bin: gh" in inspect_output


def _make_feature78_fake_openclaw_cli(bin_dir: Path, *, agent_list_json: str = "[]") -> Path:
    script = bin_dir / "openclaw"
    script.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then\n"
        "  echo 'openclaw 2026.3.31'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"agents\" ] && [ \"$2\" = \"list\" ]; then\n"
        f"  echo '{agent_list_json}'\n"
        "  exit 0\n"
        "fi\n"
        "if [ \"$1\" = \"agents\" ] && [ \"$2\" = \"add\" ]; then\n"
        "  if [ -n \"$KINNOO_OPENCLAW_INVOCATION_LOG\" ]; then\n"
        "    echo \"$*\" >> \"$KINNOO_OPENCLAW_INVOCATION_LOG\"\n"
        "  fi\n"
        "  exit 0\n"
        "fi\n"
        "echo unsupported command >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def test_feature78_import_detection_manifest_and_error_paths(tmp_path):
    fake_bin = tmp_path / "feature78-openclaw-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    _make_feature78_fake_openclaw_cli(fake_bin, agent_list_json='[{"id":"feature78-openclaw"}]')

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}{os.pathsep}{env.get('PATH', '')}"
    env["HOME"] = str(tmp_path)

    workspace = tmp_path / ".openclaw" / "workspace-feature78-openclaw"
    workspace.mkdir(parents=True, exist_ok=True)
    (workspace / "openclaw.json").write_text("{}\n", encoding="utf-8")
    (workspace / "package.json").write_text(
        "{\n"
        "  \"name\": \"feature78-openclaw\",\n"
        "  \"version\": \"1.0.0\"\n"
        "}\n",
        encoding="utf-8",
    )
    (workspace / "index.mjs").write_text("console.log('ok')\n", encoding="utf-8")

    good_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(workspace)],
        input="y\n",
        capture_output=True,
        text=True,
        env=env,
    )
    assert good_result.returncode == 0, good_result.stdout + good_result.stderr
    manifest_path = workspace / "kinnoo.yaml"
    assert manifest_path.exists()
    manifest_text = manifest_path.read_text(encoding="utf-8")
    assert "framework: openclaw" in manifest_text
    assert "language: nodejs" in manifest_text

    missing_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(tmp_path / "does-not-exist")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert missing_result.returncode != 0
    assert "import target does not exist" in (missing_result.stdout + missing_result.stderr).lower()

    file_target = tmp_path / "not-a-dir.txt"
    file_target.write_text("x\n", encoding="utf-8")
    file_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(file_target)],
        capture_output=True,
        text=True,
        env=env,
    )
    assert file_result.returncode != 0
    assert "import target must be a directory" in (file_result.stdout + file_result.stderr).lower()


def test_feature19_import_generates_requirements_via_uv_export(tmp_path):
    project_dir = tmp_path / "feature19-uv-export-requirements"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")

    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    uv_path = fake_bin / "uv"
    uv_path.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"export\" ]; then\n"
        "  echo 'requests==2.32.3'\n"
        "  exit 0\n"
        "fi\n"
        "echo 'unexpected uv invocation' >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    uv_path.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Generated requirements.txt via uv export." in output
    requirements_text = (project_dir / "requirements.txt").read_text(encoding="utf-8")
    assert requirements_text == "requests==2.32.3\n"


def test_feature19_import_generates_empty_requirements_when_detection_unavailable(tmp_path):
    project_dir = tmp_path / "feature19-empty-requirements-fallback"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text("print('hello')\n", encoding="utf-8")

    env = dict(os.environ)
    env["PATH"] = ""

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\n\n\n",
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Generated empty requirements.txt" in output
    assert (project_dir / "requirements.txt").exists()
    assert (project_dir / "requirements.txt").read_text(encoding="utf-8") == ""


def test_feature19_import_generates_requirements_from_import_inference(tmp_path):
    project_dir = tmp_path / "feature19-import-inferred-deps"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "base.py").write_text(
        "from langchain_core.agents import AgentAction\n"
        "print(AgentAction)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir)],
        input="y\nbase.py\nlangchain\n\n",
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert "Generated requirements.txt from analyzer-detected dependencies." in output
    requirements_text = (project_dir / "requirements.txt").read_text(encoding="utf-8")
    assert "langchain-core" in requirements_text


def test_feature75_adapter_inference_and_fallback(tmp_path):
    langchain_project = tmp_path / "feature75-langchain"
    langchain_project.mkdir(parents=True, exist_ok=True)
    (langchain_project / "run.py").write_text(
        "from langchain.agents import AgentExecutor\n"
        "print(AgentExecutor)\n",
        encoding="utf-8",
    )

    langchain_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(langchain_project), "--from", "langchain"],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    langchain_output = f"{langchain_result.stdout}\n{langchain_result.stderr}"
    assert langchain_result.returncode == 0, langchain_output
    assert "Applied langchain adapter" in langchain_output
    langchain_manifest = (langchain_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: langchain" in langchain_manifest
    assert "language: python" in langchain_manifest

    langgraph_project = tmp_path / "feature75-langgraph"
    langgraph_project.mkdir(parents=True, exist_ok=True)
    (langgraph_project / "graph.py").write_text(
        "from langgraph.graph import StateGraph\n"
        "print(StateGraph)\n",
        encoding="utf-8",
    )

    langgraph_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(langgraph_project), "--from", "langgraph"],
        input="y\ngraph.py\none-shot\n\n",
        capture_output=True,
        text=True,
    )
    langgraph_output = f"{langgraph_result.stdout}\n{langgraph_result.stderr}"
    assert langgraph_result.returncode == 0, langgraph_output
    assert "Applied langgraph adapter" in langgraph_output
    langgraph_manifest = (langgraph_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: langgraph" in langgraph_manifest

    openai_project = tmp_path / "feature75-openai"
    openai_project.mkdir(parents=True, exist_ok=True)
    (openai_project / "agent.py").write_text(
        "from agents import Agent\n"
        "print(Agent)\n",
        encoding="utf-8",
    )

    openai_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(openai_project), "--from", "openai"],
        input="y\nagent.py\none-shot\n\n",
        capture_output=True,
        text=True,
    )
    openai_output = f"{openai_result.stdout}\n{openai_result.stderr}"
    assert openai_result.returncode == 0, openai_output
    assert "Applied openai adapter" in openai_output
    openai_manifest = (openai_project / "kinnoo.yaml").read_text(encoding="utf-8")
    assert "framework: openai-agents" in openai_manifest

    unsupported_project = tmp_path / "feature75-fallback"
    unsupported_project.mkdir(parents=True, exist_ok=True)
    (unsupported_project / "run.py").write_text("print('hello')\n", encoding="utf-8")

    fallback_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(unsupported_project), "--from", "langgraph"],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    fallback_output = f"{fallback_result.stdout}\n{fallback_result.stderr}"
    assert fallback_result.returncode == 0, fallback_output
    assert "falling back to generic analyzer output" in fallback_output


def test_feature75_adapter_confidence_tuning_and_guidance(tmp_path):
    project_dir = tmp_path / "feature75-confidence"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "run.py").write_text(
        "from langchain.agents import AgentExecutor\n"
        "print(AgentExecutor)\n",
        encoding="utf-8",
    )

    generic_result = subprocess.run(
        [sys.executable, str(CLI_PATH), "import", str(project_dir), "--force"],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    generic_output = f"{generic_result.stdout}\n{generic_result.stderr}"
    assert generic_result.returncode == 0, generic_output

    adapter_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            str(project_dir),
            "--force",
            "--from",
            "langchain",
        ],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    adapter_output = f"{adapter_result.stdout}\n{adapter_result.stderr}"
    assert adapter_result.returncode == 0, adapter_output
    assert "Applied langchain adapter" in adapter_output
    assert "Adapter guidance:" in adapter_output

    generic_score_match = re.search(r"Framework confidence metadata:\n\s*- score: ([0-9.]+)", generic_output)
    adapter_score_match = re.search(r"Framework confidence metadata:\n\s*- score: ([0-9.]+)", adapter_output)
    assert generic_score_match is not None
    assert adapter_score_match is not None
    assert float(adapter_score_match.group(1)) >= float(generic_score_match.group(1))

    fallback_project = tmp_path / "feature75-threshold-fallback"
    fallback_project.mkdir(parents=True, exist_ok=True)
    (fallback_project / "run.py").write_text("print('no markers')\n", encoding="utf-8")

    fallback_result = subprocess.run(
        [
            sys.executable,
            str(CLI_PATH),
            "import",
            str(fallback_project),
            "--from",
            "openai",
        ],
        input="y\n\n\n",
        capture_output=True,
        text=True,
    )
    fallback_output = f"{fallback_result.stdout}\n{fallback_result.stderr}"
    assert fallback_result.returncode == 0, fallback_output
    assert "coverage is insufficient" in fallback_output
    assert "required>=0.60" in fallback_output
