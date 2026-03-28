import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = REPO_ROOT / "web"
WEB_HOST = "127.0.0.1"
WEB_PORT = int(os.environ.get("KINNOO_TEST_WEB_PORT", "3000"))
WEB_BASE_URL = f"http://{WEB_HOST}:{WEB_PORT}"


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


def test_feature49_task283_tailwind_tokens_and_dark_globals() -> None:
    tailwind_config_text = (WEB_DIR / "tailwind.config.ts").read_text(encoding="utf-8")
    globals_css_text = (WEB_DIR / "app" / "globals.css").read_text(encoding="utf-8")

    assert "bg: \"#000000\"" in tailwind_config_text
    assert "text: \"#F9FAFB\"" in tailwind_config_text
    assert "accent: \"#3B82F6\"" in tailwind_config_text
    assert "surface: \"#111111\"" in tailwind_config_text
    assert "\"card-border\": \"rgba(255,255,255,0.1)\"" in tailwind_config_text
    assert "\"Avenir Next\"" in tailwind_config_text
    assert "\"Segoe UI\"" in tailwind_config_text
    assert "card: \"8px\"" in tailwind_config_text
    assert "button: \"4px\"" in tailwind_config_text

    assert "background-color: #000000;" in globals_css_text
    assert "color: #f9fafb;" in globals_css_text.lower()
    assert "glass-surface" in globals_css_text
    assert "card-border-1" in globals_css_text


def test_feature49_task284_directory_structure() -> None:
    required_paths = [
        WEB_DIR / "app" / "(public)" / "page.tsx",
        WEB_DIR / "app" / "(public)" / "login" / "page.tsx",
        WEB_DIR / "app" / "(public)" / "signup" / "page.tsx",
        WEB_DIR / "app" / "(auth)" / "layout.tsx",
        WEB_DIR / "app" / "(auth)" / "registry" / "page.tsx",
        WEB_DIR / "components" / "ui",
        WEB_DIR / "components" / "blocks",
        WEB_DIR / "lib",
        WEB_DIR / "__tests__",
    ]

    for path in required_paths:
        assert path.exists(), f"Missing required path: {path}"


def test_feature49_task285_core_ui_dependencies_installed() -> None:
    package_json = json.loads((WEB_DIR / "package.json").read_text(encoding="utf-8"))
    deps = package_json.get("dependencies", {})

    assert "@radix-ui/react-dialog" in deps
    assert "@radix-ui/react-navigation-menu" in deps
    assert "@radix-ui/react-slot" in deps
    assert "lucide-react" in deps
    assert "framer-motion" in deps


@pytest.mark.integration
def test_feature49_task284_placeholder_routes_are_navigable() -> None:
    dev_process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--hostname", WEB_HOST, "--port", str(WEB_PORT)],
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
            if "ready" in normalized or f"localhost:{WEB_PORT}" in normalized or f"{WEB_HOST}:{WEB_PORT}" in normalized:
                started = True
                break

        assert started, f"npm run dev did not report startup on {WEB_HOST}:{WEB_PORT}"

        expected_markers = {
            "/": ["kinnoo", "feature-grid"],
            "/login": ["login"],
            "/signup": ["sign up", "signup"],
            "/registry": ["login", "registry"],
        }

        for route, markers in expected_markers.items():
            with urllib.request.urlopen(f"{WEB_BASE_URL}{route}", timeout=10) as response:
                body = response.read().decode("utf-8")
                assert response.status == 200
                normalized_body = body.lower()
                assert any(marker in normalized_body for marker in markers), (
                    f"Expected one of {markers!r} in response for route {route}, "
                    f"but response did not contain any expected marker."
                )
    finally:
        dev_process.terminate()
        try:
            dev_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            dev_process.kill()


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
        ["npm", "run", "dev", "--", "--hostname", WEB_HOST, "--port", str(WEB_PORT)],
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
            if "ready" in normalized or f"localhost:{WEB_PORT}" in normalized or f"{WEB_HOST}:{WEB_PORT}" in normalized:
                started = True
                break

        assert started, f"npm run dev did not report startup on {WEB_HOST}:{WEB_PORT}"
    finally:
        dev_process.terminate()
        try:
            dev_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            dev_process.kill()
