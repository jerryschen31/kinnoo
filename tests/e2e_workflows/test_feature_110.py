from __future__ import annotations

from pathlib import Path
import subprocess


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_feature110_group1() -> None:
    signup_page = _read("web/app/(public)/signup/page.tsx")
    landing_page = _read("web/app/(public)/page.tsx")

    assert "Sign up is currently invite-only. Please contact me for early access." in signup_page
    assert "Contact Me" in signup_page
    assert "https://twitter.com/messages/compose?recipient_id=4118511499" in signup_page

    assert "Send Verification Link" not in signup_page
    assert "register-request" not in signup_page

    # AC1 guardrail: keep the landing page title unchanged.
    assert "The package manager for AI agents" in landing_page


def test_feature110_group2() -> None:
    login_page = _read("web/app/(public)/login/page.tsx")
    registry_page = _read("web/app/(auth)/registry/page.tsx")
    source_roots = [Path("web/app"), Path("web/components"), Path("web/lib")]
    web_files = [
        path
        for root in source_roots
        for path in list(root.rglob("*.tsx")) + list(root.rglob("*.ts"))
    ]
    web_source = "\n".join(path.read_text(encoding="utf-8") for path in web_files)

    assert 'router.push("/registry")' in login_page
    assert "fetchMyAgents" in registry_page
    assert "RegistryTabs" in registry_page

    assert "mailto:" not in web_source
    assert "Email us" not in web_source

    build_result = subprocess.run(
        ["npm", "run", "build"],
        cwd="web",
        check=False,
        capture_output=True,
        text=True,
    )
    assert build_result.returncode == 0, build_result.stdout + "\n" + build_result.stderr
