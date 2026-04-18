import subprocess
import sys
import os
import signal
import time
from pathlib import Path


CLI_PATH = Path(__file__).resolve().parents[2] / "src" / "kinnoo" / "cli.py"


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
    assert "language: nodejs" in manifest_text
    assert "type: daemon" in manifest_text
    assert "package_manager: pnpm" in manifest_text
    assert "skills:" in manifest_text
    assert "skills/default/SKILL.md" in manifest_text
    assert "state_dirs:" in manifest_text
    assert "- memory" in manifest_text


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
