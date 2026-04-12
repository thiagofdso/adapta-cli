from __future__ import annotations

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


def test_debate_command_interactively_creates_debate_json(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ADAPTA_DEBATE_CONFIG", raising=False)
    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: DummyClient())

    result = runner.invoke(
        app,
        ["debate", "--prompt", "Defina uma arquitetura"],
        input="2\n1\narquiteto\n4\ndesenvolvedor\n2\n",
    )

    assert result.exit_code == 0, result.stderr
    assert (tmp_path / "debate.json").exists()
    assert "Conclusão Final" in result.stdout
