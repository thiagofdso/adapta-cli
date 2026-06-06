from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import adapta.cli as cli_module
from adapta.cli import app
from adapta.config import Settings
from adapta.services import persona_service


class IntegrationClient:
    def __init__(
        self,
        response_text: str = "<<<PERSONA_CONTENT_START>>>\n# Persona\n<<<PERSONA_CONTENT_END>>>",
    ) -> None:
        self.response_text = response_text
        self.deleted_chats: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        return self.response_text

    async def delete_chat(self, chat_id: str) -> None:
        self.deleted_chats.append(chat_id)


def test_persona_command_saves_minimal_persona(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    client = IntegrationClient()

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
        ["persona"],
        input="Ana Lider\nGerente de Produto\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n",
    )

    output_path = tmp_path / ".adapta" / "persona" / "ana-lider.md"
    json_path = tmp_path / ".adapta" / "persona" / "ana-lider.json"
    assert result.exit_code == 0, result.stderr
    assert output_path.exists()
    assert json_path.exists()
    assert output_path.read_text(encoding="utf-8") == "# Persona\n"
    assert '"cargo": "Gerente de Produto"' in json_path.read_text(encoding="utf-8")
    assert client.deleted_chats


def test_persona_command_can_regenerate_from_input_file(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    client = IntegrationClient(
        response_text="<<<PERSONA_CONTENT_START>>>\n# Persona Atualizada\n<<<PERSONA_CONTENT_END>>>"
    )
    input_file = tmp_path / "persona.json"
    input_file.write_text(
        '{"nome":"Ana Lider","cargo":"Gerente de Produto","setor":"SaaS"}',
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

    result = runner.invoke(app, ["persona", "--input-file", str(input_file)])

    output_path = tmp_path / ".adapta" / "persona" / "ana-lider.md"
    assert result.exit_code == 0, result.stderr
    assert output_path.read_text(encoding="utf-8") == "# Persona Atualizada\n"


def test_persona_command_preserves_existing_file_when_overwrite_is_rejected(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    client = IntegrationClient(
        response_text="<<<PERSONA_CONTENT_START>>>\n# Nova Persona\n<<<PERSONA_CONTENT_END>>>"
    )
    output_path = tmp_path / ".adapta" / "persona" / "ana-lider.md"
    output_path.parent.mkdir(parents=True)
    output_path.write_text("# Anterior\n", encoding="utf-8")

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

    result = runner.invoke(app, ["persona"], input="Ana Lider\nn\n")

    assert result.exit_code == 0, result.stderr
    assert output_path.read_text(encoding="utf-8") == "# Anterior\n"
    assert client.deleted_chats == []
