from pathlib import Path


def test_makefile_exposes_required_targets() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")

    assert "test:" in content
    assert "prompt:" in content
    assert "chat:" in content
    assert "install:" in content
    assert "install-local:" in content
    assert "install-remote:" in content


def test_makefile_prompt_target_uses_cli_module() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")

    assert "-m adapta.cli" in content


def test_makefile_install_targets_use_scripts() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")

    assert "scripts/install-local.sh" in content
    assert "scripts/install-remote.sh" in content
    assert "REMOTE_REPO" in content
    assert "PIPX" in content
