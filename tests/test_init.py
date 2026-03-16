def test_gemini_template_uses_genai_and_flash_lite(tmp_path):
    """Test that Gemini template uses google-genai and gemini-2.5-flash-lite (test39).
    This covers test39 in TESTS.txt."""
    agent_name = "gemini-flash-lite-agent"
    code, out, err = run_cli(["init", agent_name, "--framework", "gemini"], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    # requirements.txt should contain google-genai and NOT google-generativeai
    reqs = (agent_dir / "requirements.txt").read_text()
    assert "google-genai" in reqs, "google-genai should be in requirements.txt"
    assert "google-generativeai" not in reqs, "google-generativeai should NOT be in requirements.txt"
    # run.py should reference gemini-2.5-flash-lite
    runpy = (agent_dir / "run.py").read_text()
    assert "gemini-2.5-flash-lite" in runpy, "run.py should reference gemini-2.5-flash-lite"
    # README.md should mention GOOGLE_API_KEY and usage
    readme = (agent_dir / "README.md").read_text()
    assert "GOOGLE_API_KEY" in readme, "README.md should mention GOOGLE_API_KEY"
    assert "python run.py" in readme, "README.md should show run.py usage"
import pytest

@pytest.mark.parametrize("framework,dep,envvar,run_example,model_hint,test_id", [
    ("gemini", "google-genai", "GOOGLE_API_KEY", "Hello Gemini!", "gemini-2.5-flash-lite", "test29"),
    ("chatgpt", "openai", "OPENAI_API_KEY", "Hello ChatGPT!", "gpt-5-nano", "test30"),
    ("claude-chat", "anthropic", "ANTHROPIC_API_KEY", "Hello Claude!", "claude-sonnet-4-20250514", "test31"),
])
def test_framework_templates_generate_correct_files(framework, dep, envvar, run_example, model_hint, test_id):
    import tempfile
    from pathlib import Path
    import os
    agent_name = f"test_{framework}"
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = run_kinnoo_init([agent_name, "--framework", framework])
        finally:
            os.chdir(cwd)
        assert result.returncode == 0, f"Framework {framework} should succeed"
        agent_dir = Path(tmpdir) / agent_name
        # Directory and files
        assert agent_dir.exists()
        for fname in ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]:
            assert (agent_dir / fname).exists(), f"{fname} missing for {framework}"
        # requirements.txt
        reqs = (agent_dir / "requirements.txt").read_text()
        assert dep in reqs, f"Dependency {dep} missing in requirements.txt for {framework}"
        # README.md
        readme = (agent_dir / "README.md").read_text()
        assert envvar in readme, f"API key env var {envvar} missing in README for {framework}"
        assert run_example in readme, f"Run example missing in README for {framework}"
        # run.py
        runpy = (agent_dir / "run.py").read_text()
        assert model_hint in runpy, f"Model hint {model_hint} missing in run.py for {framework}"
        # tools/ and prompts/
        assert (agent_dir / "tools").is_dir()
        assert (agent_dir / "prompts").is_dir()
import os
import shutil
import subprocess
import tempfile
import sys

KINNOO_INIT_PATH = os.path.join(os.path.dirname(__file__), '../src/kinnoo/init_command.py')

def run_kinnoo_init(args):
    cmd = [sys.executable, KINNOO_INIT_PATH] + args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result

def test_framework_valid():
    # Should not error for supported frameworks (no file creation yet)
    import tempfile
    for fw in ["gemini", "chatgpt", "claude-chat"]:
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_name = f"myagent_{fw}"
            cwd = os.getcwd()
            os.chdir(tmpdir)
            result = run_kinnoo_init([agent_name, "--framework", fw])
            os.chdir(cwd)
            assert result.returncode == 0, f"Valid framework {fw} should not error"

def test_framework_invalid():
    # Should error for unsupported frameworks
    import tempfile
    for fw in ["pigglypoo", "openai", "invalid-name"]:
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                result = run_kinnoo_init(["myagent", "--framework", fw])
            finally:
                os.chdir(cwd)
        assert result.returncode != 0, f"Invalid framework {fw} should error"
        assert b"Unsupported framework" in result.stderr, f"Error message missing for {fw}"
        assert b"Usage: kinnoo init" in result.stderr, f"Usage message missing for {fw}"

def test_missing_agent_name():
    # Should error and print usage if agent_name is missing
    result = run_kinnoo_init(["--framework", "gemini"])
    assert result.returncode != 0, "Missing agent_name should error"
    assert b"Usage: kinnoo init" in result.stderr, "Usage message missing for missing agent_name"
import subprocess
import sys
import re
import os
import pytest
from pathlib import Path

KINNOO_CLI = [sys.executable, "-m", "kinnoo.cli"]


def run_cli(args, cwd=None):
    """Run kinnoo CLI with args, return (exit_code, stdout, stderr)"""
    proc = subprocess.Popen(
        [sys.executable, "-m", "kinnoo.cli"] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        text=True,
    )
    out, err = proc.communicate()
    return proc.returncode, out, err


import pytest

@pytest.mark.parametrize("test_id,cli_args", [
    ("test7", ["init"]),
    ("test33", ["init"]),
])
def test_init_missing_name_prints_usage(tmp_path, test_id, cli_args):
    code, out, err = run_cli(cli_args, cwd=tmp_path)
    assert code != 0
    assert "Usage" in err
    assert "<agent-name>" in err

def test_init_invalid_name_rejected(tmp_path):
    invalid_names = ["_invalid-name", "My Agent", "MyAgent"]
    for name in invalid_names:
        code, out, err = run_cli(["init", name], cwd=tmp_path)
        assert code != 0
        assert "Invalid agent name" in err


def test_init_creates_directory_structure(tmp_path):
    agent_name = "test-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None  # dry-run or success
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    expected_files = ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]
    for fname in expected_files:
        assert (agent_dir / fname).exists()
    assert (agent_dir / "tools").is_dir()
    assert (agent_dir / "prompts").is_dir()


import pytest

@pytest.mark.parametrize("test_id,agent_name", [
    ("test10", "test-agent"),
    ("test37", "test-agent"),
])
def test_generated_manifest_passes_validation(tmp_path, test_id, agent_name):
    run_cli(["init", agent_name], cwd=tmp_path)
    from kinnoo.validator import validate
    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors


def test_generated_entrypoint_executes(tmp_path):
    agent_name = "test-agent"
    run_cli(["init", agent_name], cwd=tmp_path)
    run_py = tmp_path / agent_name / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "hello"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout


def test_generated_entrypoint_has_asyncio(tmp_path):
    agent_name = "test-agent"
    run_cli(["init", agent_name], cwd=tmp_path)
    run_py = tmp_path / agent_name / "run.py"
    contents = run_py.read_text()
    assert "asyncio.run" in contents
    assert "async def" in contents


import pytest

@pytest.mark.parametrize("test_id,agent_name", [
    ("test13", "test-agent"),
    ("test34", "test-agent"),
])
def test_init_existing_directory_fails(tmp_path, test_id, agent_name):
    agent_dir = tmp_path / agent_name
    agent_dir.mkdir()
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code != 0
    assert "already exists" in err
    # Directory should be unchanged (still exists)
    assert agent_dir.exists() and agent_dir.is_dir()


def test_init_full_workflow(tmp_path):
    agent_name = "my-first-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    # Directory and files exist
    assert agent_dir.exists() and agent_dir.is_dir()
    for fname in ["kinnoo.yaml", "run.py", "requirements.txt", "README.md"]:
        assert (agent_dir / fname).exists()
    assert (agent_dir / "tools").is_dir()
    assert (agent_dir / "prompts").is_dir()
    # Manifest passes validation
    from kinnoo.validator import validate
    manifest_path = agent_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors
    # Entrypoint runs successfully
    run_py = agent_dir / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "test"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout


import pytest

@pytest.mark.parametrize("framework,test_id", [
    ("gemini", "test32"),
    ("chatgpt", "test32"),
    ("claude-chat", "test32"),
])
def test_framework_manifests_pass_validation(framework, test_id):
    import tempfile
    from pathlib import Path
    from kinnoo.validator import validate
    import os
    agent_name = f"validate-{framework}"
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            result = run_kinnoo_init([agent_name, "--framework", framework])
            assert result.returncode == 0, f"Framework {framework} should succeed"
            manifest_path = Path(tmpdir) / agent_name / "kinnoo.yaml"
            is_valid, errors = validate(str(manifest_path))
            assert is_valid, f"Manifest for {framework} should be valid, got errors: {errors}"
            assert not errors, f"Manifest for {framework} should have no errors, got: {errors}"
        finally:
            os.chdir(cwd)


def test_init_vanilla_agent(tmp_path):
    agent_name = "vanilla-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    # requirements.txt should be empty (vanilla agent)
    reqs = (agent_dir / "requirements.txt").read_text()
    assert reqs.strip() == ""
    # README.md should not mention any API key
    readme = (agent_dir / "README.md").read_text()
    assert "API key" not in readme
    # run.py should be the hello-world template
    runpy = (agent_dir / "run.py").read_text()
    assert "Hello, world!" in runpy


def test_agent_name_with_underscore_is_accepted(tmp_path):
    agent_name = "agent_with_underscore"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None
    agent_dir = tmp_path / agent_name
    assert agent_dir.exists() and agent_dir.is_dir()
    # Manifest passes validation
    from kinnoo.validator import validate
    manifest_path = agent_dir / "kinnoo.yaml"
    is_valid, errors = validate(str(manifest_path))
    assert is_valid
    assert not errors
    # Entrypoint runs successfully
    run_py = agent_dir / "run.py"
    result = subprocess.run([sys.executable, str(run_py), "test"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Hello, world!" in result.stdout


def test_feature21_framework_invalid_lists_all_choices(tmp_path):
    code, out, err = run_cli(["init", "feature21-invalid", "--framework", "invalid-name"], cwd=tmp_path)
    assert code != 0
    for framework in [
        "gemini",
        "chatgpt",
        "claude-chat",
        "pydantic-ai",
        "langgraph",
        "openai-agents",
    ]:
        assert framework in err


def test_feature21_framework_values_accepted(tmp_path):
    for framework in ["pydantic-ai", "langgraph", "openai-agents"]:
        agent_name = f"feature21-{framework}-agent"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0
        agent_dir = tmp_path / agent_name
        assert agent_dir.exists() and agent_dir.is_dir()


def test_feature21_pydanticai_template_generation(tmp_path):
    agent_name = "feature21-pydanticai-template"
    code, out, err = run_cli(["init", agent_name, "--framework", "pydantic-ai"], cwd=tmp_path)
    assert code == 0

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "README.md").exists()

    run_py = (agent_dir / "run.py").read_text()
    readme = (agent_dir / "README.md").read_text()
    assert "pydantic-ai template" in run_py
    assert "pydantic-ai" in readme


def test_feature21_langgraph_template_generation(tmp_path):
    agent_name = "feature21-langgraph-template"
    code, out, err = run_cli(["init", agent_name, "--framework", "langgraph"], cwd=tmp_path)
    assert code == 0

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "README.md").exists()

    run_py = (agent_dir / "run.py").read_text()
    readme = (agent_dir / "README.md").read_text()
    assert "langgraph template" in run_py
    assert "langgraph" in readme


def test_feature21_openai_agents_template_generation(tmp_path):
    agent_name = "feature21-openai-agents-template"
    code, out, err = run_cli(["init", agent_name, "--framework", "openai-agents"], cwd=tmp_path)
    assert code == 0

    agent_dir = tmp_path / agent_name
    assert (agent_dir / "run.py").exists()
    assert (agent_dir / "requirements.txt").exists()
    assert (agent_dir / "kinnoo.yaml").exists()
    assert (agent_dir / "README.md").exists()

    run_py = (agent_dir / "run.py").read_text()
    readme = (agent_dir / "README.md").read_text()
    assert "openai-agents template" in run_py
    assert "openai-agents" in readme


def test_feature21_requirements_major_version_pins(tmp_path):
    expected_dependency_patterns = {
        "pydantic-ai": r"^pydantic-ai>=\d+\.\d+,<\d+\.\d+$",
        "langgraph": r"^langgraph>=\d+\.\d+,<\d+\.\d+$",
        "openai-agents": r"^openai-agents>=\d+\.\d+,<\d+\.\d+$",
    }

    for framework, dependency_pattern in expected_dependency_patterns.items():
        agent_name = f"feature21-pins-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0

        requirements_path = tmp_path / agent_name / "requirements.txt"
        requirements_entry = requirements_path.read_text().strip()
        assert re.match(dependency_pattern, requirements_entry), (
            f"Requirements pin for {framework} did not match expected major-range format: {requirements_entry}"
        )


def test_feature21_manifests_pass_and_set_framework(tmp_path):
    import yaml
    from kinnoo.validator import validate

    frameworks = ["pydantic-ai", "langgraph", "openai-agents"]
    for framework in frameworks:
        agent_name = f"feature21-manifest-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0

        manifest_path = tmp_path / agent_name / "kinnoo.yaml"
        is_valid, errors = validate(str(manifest_path))
        assert is_valid, f"Manifest for {framework} should validate: {errors}"
        assert not errors

        manifest_data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        assert manifest_data.get("framework") == framework


def test_feature21_readme_setup_guidance(tmp_path):
    readme_expectations = {
        "pydantic-ai": ["OPENAI_API_KEY", "Model Configuration", "python run.py"],
        "langgraph": ["OPENAI_API_KEY", "Graph Configuration", "python run.py"],
        "openai-agents": ["OPENAI_API_KEY", "Agent Configuration", "python run.py"],
    }

    for framework, expected_terms in readme_expectations.items():
        agent_name = f"feature21-readme-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0

        readme_text = (tmp_path / agent_name / "README.md").read_text()
        for term in expected_terms:
            assert term in readme_text


def test_feature21_regression_existing_frameworks_unchanged(tmp_path):
    expected = {
        "gemini": {
            "dependency": "google-genai",
            "env_var": "GOOGLE_API_KEY",
            "model_hint": "gemini-2.5-flash-lite",
            "run_example": "Hello Gemini!",
        },
        "chatgpt": {
            "dependency": "openai",
            "env_var": "OPENAI_API_KEY",
            "model_hint": "gpt-5-nano",
            "run_example": "Hello ChatGPT!",
        },
        "claude-chat": {
            "dependency": "anthropic",
            "env_var": "ANTHROPIC_API_KEY",
            "model_hint": "claude-sonnet-4-20250514",
            "run_example": "Hello Claude!",
        },
    }

    for framework, checks in expected.items():
        agent_name = f"feature21-regression-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        agent_dir = tmp_path / agent_name
        requirements_text = (agent_dir / "requirements.txt").read_text()
        run_text = (agent_dir / "run.py").read_text()
        readme_text = (agent_dir / "README.md").read_text()

        assert checks["dependency"] in requirements_text
        assert checks["model_hint"] in run_text
        assert checks["env_var"] in readme_text
        assert checks["run_example"] in readme_text

        from kinnoo.validator import validate
        manifest_path = agent_dir / "kinnoo.yaml"
        is_valid, errors = validate(str(manifest_path))
        assert is_valid
        assert not errors


def _feature21_tested_compatibility_targets():
    # Keep this map aligned with template requirements constants.
    return {
        "pydantic-ai": "pydantic-ai>=0.0,<0.1",
        "langgraph": "langgraph>=0.2,<0.3",
        "openai-agents": "openai-agents>=0.1,<0.2",
    }


def _satisfies_feature21_dependency_policy(requirement_line: str) -> bool:
    exact_match = re.match(r"^[a-z0-9-]+==\d+\.\d+\.\d+$", requirement_line)
    if exact_match:
        return True

    bounded_range = re.match(
        r"^(?P<pkg>[a-z0-9-]+)>=(?P<lmajor>\d+)\.(?P<lminor>\d+),<(?P<umajor>\d+)\.(?P<uminor>\d+)$",
        requirement_line,
    )
    if not bounded_range:
        return False

    lower_major = int(bounded_range.group("lmajor"))
    lower_minor = int(bounded_range.group("lminor"))
    upper_major = int(bounded_range.group("umajor"))
    upper_minor = int(bounded_range.group("uminor"))

    if lower_major >= 1:
        # Stable-major policy: bounded major range (>=X.Y,<X+1.0).
        return upper_major == (lower_major + 1) and upper_minor == 0

    # Pre-1.0 policy: explicitly tested bounded range narrower than <1.0.
    return upper_major == 0 and upper_minor == (lower_minor + 1)


def test_feature21_requirements_tested_compatibility_ranges(tmp_path):
    expected_requirements = _feature21_tested_compatibility_targets()

    for framework, expected_line in expected_requirements.items():
        agent_name = f"feature21-compat-ranges-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        requirements_line = (tmp_path / agent_name / "requirements.txt").read_text().strip()
        assert requirements_line == expected_line
        assert "<1.0" not in requirements_line
        assert _satisfies_feature21_dependency_policy(requirements_line)


def test_feature21_dependency_policy_alignment(tmp_path):
    features_text = Path("FEATURES.txt").read_text(encoding="utf-8")
    assert "stable major versions" in features_text
    assert "pre-1.0 frameworks" in features_text
    assert "tested compatibility ranges" in features_text

    for framework in _feature21_tested_compatibility_targets().keys():
        agent_name = f"feature21-policy-alignment-{framework}"
        code, out, err = run_cli(["init", agent_name, "--framework", framework], cwd=tmp_path)
        assert code == 0, err

        requirements_line = (tmp_path / agent_name / "requirements.txt").read_text().strip()
        assert _satisfies_feature21_dependency_policy(requirements_line), (
            f"Generated requirement does not satisfy AC4 policy for {framework}: {requirements_line}"
        )


def test_feature21_pydantic_ai_framework_native_template(tmp_path):
    agent_name = "feature21-pydantic-ai-native"
    code, out, err = run_cli(["init", agent_name, "--framework", "pydantic-ai"], cwd=tmp_path)
    assert code == 0, err

    run_text = (tmp_path / agent_name / "run.py").read_text()
    assert "from pydantic_ai import Agent" in run_text
    assert "Agent(" in run_text
    assert "_run_framework_mode" in run_text
    assert "KINNOO_TEST_SAFE_MODE" in run_text
    assert "test-safe response" in run_text
    assert "Placeholder scaffold for pydantic-ai workflow" not in run_text


def test_feature9_init_manifest_includes_description_and_author(tmp_path):
    """test75: init-generated manifest includes description and author placeholders."""
    agent_name = "feature9-init-agent"
    code, out, err = run_cli(["init", agent_name], cwd=tmp_path)
    assert code == 0 or code is None

    manifest_path = tmp_path / agent_name / "kinnoo.yaml"
    assert manifest_path.exists()

    import yaml

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert "description" in manifest
    assert isinstance(manifest["description"], str)
    assert manifest["description"].strip() != ""

    assert "author" in manifest
    assert isinstance(manifest["author"], str)
    assert manifest["author"].strip() != ""
