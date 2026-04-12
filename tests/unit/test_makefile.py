from pathlib import Path


def test_makefile_exposes_required_targets() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")

    assert "test:" in content
    assert "prompt:" in content
    assert "chat:" in content


def test_makefile_prompt_target_uses_cli_module() -> None:
    content = Path("Makefile").read_text(encoding="utf-8")

    assert "-m adapta.cli" in content
