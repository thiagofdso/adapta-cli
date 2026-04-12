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
        return "2"

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        return "2"

    async def delete_chat(self, chat_id: str) -> None:
        return None


def test_prompt_command_prints_response(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

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
        [
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
        ],
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == "2"


def test_models_command_lists_available_models() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["models"])

    assert result.exit_code == 0
    assert "gpt\tGPT-5\tGPT_5" in result.stdout
    assert "claude\tClaude 4.5 Sonnet\tCLAUDE_4_5_SONNET" in result.stdout


def test_prompt_command_writes_output_file(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    output_file = tmp_path / "saida.txt"

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
        [
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0
    assert output_file.read_text(encoding="utf-8").strip() == "2"


def test_chat_command_runs_until_exit(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

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
        app, ["chat", "--model", "gpt"], input="quanto é 1+1\nexit\n"
    )

    assert result.exit_code == 0
    assert "2" in result.stdout


def test_prompt_command_uses_default_model(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model="gpt",
            env_file_path=tmp_path / ".env",
        ),
    )
    monkeypatch.setattr(cli_module, "create_client", lambda settings: DummyClient())

    result = runner.invoke(
        app, ["prompt", "--prompt", "quanto é 1+1 responda somente o valor"]
    )

    assert result.exit_code == 0
    assert result.stdout.strip() == "2"


def test_prompt_command_shows_friendly_error_without_traceback(monkeypatch) -> None:
    runner = CliRunner()

    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: (_ for _ in ()).throw(
            ValueError("ADAPTA_LOGIN e ADAPTA_PASSWORD são obrigatórios.")
        ),
    )

    result = runner.invoke(
        app,
        [
            "prompt",
            "--model",
            "gpt",
            "--prompt",
            "quanto é 1+1 responda somente o valor",
        ],
    )

    assert result.exit_code == 1
    assert "ADAPTA_LOGIN e ADAPTA_PASSWORD são obrigatórios." in result.stderr
    assert "Traceback" not in result.stderr


def test_debate_command_reprompts_invalid_agent_count(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()

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
        input="abc\n1\n2\n1\narquiteto\n4\ndesenvolvedor\nxyz\n2\n",
    )

    assert result.exit_code == 0, result.stderr
    assert "Informe um número inteiro válido." in result.stdout
    assert "Informe um número maior ou igual a 2." in result.stdout
    assert (tmp_path / "debate.json").exists()
