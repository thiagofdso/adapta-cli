from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import adapta.cli as cli_module
from adapta.cli import app
from adapta.config import Settings


class DummyClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        return "conclusao final"

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        return f"{model_backend}:{len(messages)}"

    async def delete_chat(self, chat_id: str | list[str]) -> None:
        return None


def test_debate_command_writes_output_file(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    config_path = tmp_path / "debate.json"
    output_path = tmp_path / "resultado.md"
    config_path.write_text(
        json.dumps(
            {
                "A1": {"model": "claude", "prompt": "arquiteto"},
                "A2": {"model": "gpt", "prompt": "dev"},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env", data_dir=tmp_path / "data",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: DummyClient())

    result = runner.invoke(
        app,
        [
            "debate",
            "--config",
            str(config_path),
            "--prompt",
            "Defina uma arquitetura",
            "--rounds",
            "2",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert str(output_path) in result.stdout
    content = output_path.read_text(encoding="utf-8")
    assert "# Debate Results" in content
    assert "## Final Conclusion" in content
