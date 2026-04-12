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
        raise RuntimeError("falha remota")

    async def delete_chat(self, chat_id: str | list[str]) -> None:
        return None

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, object]], chat_id: str
    ) -> str:
        return "conteudo gerado"


def test_destilador_reports_cleanup_warning(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    pdf_path = tmp_path / "livro.pdf"
    output_path = tmp_path / "saida.md"
    pdf_path.write_bytes(b"%PDF-1.4\n")

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
        ["destilador", "--input", str(pdf_path), "--output", str(output_path)],
    )

    assert result.exit_code == 0, result.stderr
    assert "Falha ao limpar" in result.stderr
