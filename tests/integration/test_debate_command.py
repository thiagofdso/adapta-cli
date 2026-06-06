from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

import adapta.cli as cli_module
from adapta.cli import app
from adapta.config import Settings
from adapta.services import persona_service


class DummyClient:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.uploaded: list[str] = []
        self.chat_calls: list[
            tuple[str, str, list[dict[str, str]], list[str] | None]
        ] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        return "conclusao final"

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        self.chat_calls.append((model_backend, chat_id, list(messages), None))
        return f"{model_backend}:{len(messages)}"

    async def chat_with_files(
        self,
        *,
        model_backend: str,
        messages: list[dict[str, str]],
        chat_id: str,
        files: list[dict[str, object]],
    ) -> str:
        self.chat_calls.append(
            (
                model_backend,
                chat_id,
                list(messages),
                [str(file["filename"]) for file in files],
            )
        )
        return f"{model_backend}:{len(messages)}"

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        self.uploaded.append(file_path.name)
        return {
            "filename": file_path.name,
            "url": f"https://files.example/{file_path.name}",
            "size": file_path.stat().st_size,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    async def delete_chat(self, chat_id: str | list[str]) -> None:
        if isinstance(chat_id, list):
            self.deleted.extend(chat_id)
        else:
            self.deleted.append(chat_id)


def test_debate_command_runs_with_config_file(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    config_path = tmp_path / "debate.json"
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
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

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
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "A1 Rodada 1" in result.stdout
    assert "A2 Rodada 2" in result.stdout
    assert "Conclusão Final" in result.stdout


def test_debate_command_accepts_prompt_file(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    config_path = tmp_path / "debate.json"
    prompt_path = tmp_path / "tema.txt"
    prompt_path.write_text(
        "Defina uma arquitetura orientada a eventos", encoding="utf-8"
    )
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
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "debate",
            "--config",
            str(config_path),
            "--prompt-file",
            str(prompt_path),
            "--rounds",
            "1",
        ],
    )

    assert result.exit_code == 0, result.stderr
    first_prompt = client.chat_calls[0][2][0]["content"]
    expected_topic = 'Tema do debate: "Defina uma arquitetura orientada a eventos".'
    assert expected_topic in first_prompt


def test_debate_command_rejects_multiple_prompt_sources(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    client = DummyClient()
    config_path = tmp_path / "debate.json"
    prompt_path = tmp_path / "tema.txt"
    prompt_path.write_text(
        "Defina uma arquitetura orientada a eventos", encoding="utf-8"
    )
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
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "debate",
            "--config",
            str(config_path),
            "--prompt",
            "Tema inline",
            "--prompt-file",
            str(prompt_path),
            "--rounds",
            "1",
        ],
    )

    assert result.exit_code == 1
    assert "Use apenas uma das opções: --prompt ou --prompt-file." in result.stderr


def test_debate_command_accepts_file_attachments(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    config_path = tmp_path / "debate.json"
    attachment_a = tmp_path / "a.pdf"
    attachment_b = tmp_path / "b.pdf"
    config_path.write_text(
        json.dumps(
            {
                "A1": {"model": "claude", "prompt": "arquiteto"},
                "A2": {"model": "gpt", "prompt": "dev"},
            }
        ),
        encoding="utf-8",
    )
    attachment_a.write_bytes(b"%PDF-1.4\n")
    attachment_b.write_bytes(b"%PDF-1.4\n")

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
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

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
            "--file",
            f"{attachment_a},{attachment_b}",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert client.uploaded == ["a.pdf", "b.pdf"]
    assert len(client.chat_calls) == 4
    assert all(call[3] == ["a.pdf", "b.pdf"] for call in client.chat_calls)


def test_debate_command_accepts_optional_persona_file_per_agent(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    client = DummyClient()
    config_path = tmp_path / "debate.json"
    persona_path = tmp_path / "persona.md"
    persona_path.write_text(
        "# Você é Cliente Premium\nDefenda qualidade.", encoding="utf-8"
    )
    config_path.write_text(
        json.dumps(
            {
                "A1": {
                    "model": "claude",
                    "prompt": "arquiteto",
                    "persona": "persona.md",
                },
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
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "debate",
            "--config",
            str(config_path),
            "--prompt",
            "Defina uma arquitetura",
            "--rounds",
            "1",
        ],
    )

    assert result.exit_code == 0, result.stderr
    first_prompt = client.chat_calls[0][2][0]["content"]
    assert "# Você é Cliente Premium" in first_prompt


def test_debate_command_accepts_persona_short_name(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    config_path = tmp_path / "debate.json"
    persona_dir = tmp_path / ".adapta" / "persona"
    persona_dir.mkdir(parents=True)
    (persona_dir / "cliente-cetico.md").write_text(
        "# Você é Cliente Cético\nQuestione promessas.",
        encoding="utf-8",
    )
    config_path.write_text(
        json.dumps(
            {
                "A1": {
                    "model": "claude",
                    "prompt": "arquiteto",
                    "persona": "cliente-cetico",
                },
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
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)
    monkeypatch.setattr(persona_service.Path, "home", lambda: tmp_path)

    result = runner.invoke(
        app,
        [
            "debate",
            "--config",
            str(config_path),
            "--prompt",
            "Defina uma arquitetura",
            "--rounds",
            "1",
        ],
    )

    assert result.exit_code == 0, result.stderr
    first_prompt = client.chat_calls[0][2][0]["content"]
    assert "# Você é Cliente Cético" in first_prompt


def test_debate_command_supports_control_mode(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = DummyClient()
    config_path = tmp_path / "debate.json"
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
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

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
            "--control",
        ],
        input="1\n6\n",
    )

    assert result.exit_code == 0, result.stderr
    assert "1. Continuar fluxo atual" in result.stdout
    assert "Conclusão Final" in result.stdout
