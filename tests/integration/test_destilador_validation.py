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

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        return {
            "filename": file_path.name,
            "url": f"https://example.invalid/{file_path.name}",
            "size": 10,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    async def delete_file(self, file_path: str) -> None:
        return None

    async def delete_chat(self, chat_id: str | list[str]) -> None:
        return None

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, object]], chat_id: str
    ) -> str:
        return f"saida {chat_id}"


def test_destilador_command_accepts_input_with_output_dir(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    output_dir = tmp_path / "saidas"

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
            "destilador",
            "--input",
            str(pdf_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert (output_dir / "livro.md").exists()
