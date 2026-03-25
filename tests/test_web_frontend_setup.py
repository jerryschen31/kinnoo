import json
import subprocess
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = REPO_ROOT / "web"


def _major_version(version: str) -> int:
    clean = version.lstrip("^~>=< ")
    return int(clean.split(".", maxsplit=1)[0])


def test_feature49_task282_scaffolded_nextjs_project() -> None:
    package_json_path = WEB_DIR / "package.json"
    tsconfig_path = WEB_DIR / "tsconfig.json"
    tailwind_config_path = WEB_DIR / "tailwind.config.ts"
    nvmrc_path = WEB_DIR / ".nvmrc"

    assert package_json_path.exists(), "web/package.json must exist"
    assert tsconfig_path.exists(), "web/tsconfig.json must exist"
    assert tailwind_config_path.exists(), "web/tailwind.config.ts must exist"
    assert nvmrc_path.read_text(encoding="utf-8").strip() == "20"

    package_json = json.loads(package_json_path.read_text(encoding="utf-8"))
    deps = package_json.get("dependencies", {})
    dev_deps = package_json.get("devDependencies", {})

    assert _major_version(deps.get("next", "0")) >= 15
    assert _major_version(deps.get("react", "0")) >= 19
    assert "typescript" in dev_deps
    assert "tailwindcss" in dev_deps


@pytest.mark.integration
def test_feature49_task282_build_and_dev_start() -> None:
    build_result = subprocess.run(
        ["npm", "run", "build"],
        cwd=WEB_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    assert build_result.returncode == 0, build_result.stdout + build_result.stderr

    dev_process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--hostname", "127.0.0.1", "--port", "3000"],
        cwd=WEB_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        started = False
        deadline = time.time() + 45
        assert dev_process.stdout is not None
        while time.time() < deadline:
            line = dev_process.stdout.readline()
            if not line:
                if dev_process.poll() is not None:
                    break
                continue
            normalized = line.lower()
            if "ready" in normalized or "localhost:3000" in normalized:
                started = True
                break

        assert started, "npm run dev did not report startup on localhost:3000"
    finally:
        dev_process.terminate()
        try:
            dev_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            dev_process.kill()
