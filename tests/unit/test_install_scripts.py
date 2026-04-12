from pathlib import Path


def test_install_local_script_uses_pip_install() -> None:
    content = Path("scripts/install-local.sh").read_text(encoding="utf-8")

    assert "-m pip install" in content


def test_install_remote_script_supports_git_url() -> None:
    content = Path("scripts/install-remote.sh").read_text(encoding="utf-8")

    assert "git+$REPO_URL" in content
