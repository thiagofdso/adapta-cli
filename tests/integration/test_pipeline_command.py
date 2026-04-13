from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import adapta.cli as cli_module
from adapta.cli import app
from adapta.config import Settings


class DummyPipelineClient:
    def __init__(self) -> None:
        self.uploaded: list[Path] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        self.uploaded.append(file_path)
        return {
            "filename": file_path.name,
            "url": f"https://example.invalid/{file_path.name}",
            "size": file_path.stat().st_size,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    async def delete_file(self, file_path: str) -> None:
        return None

    async def prompt_with_files(
        self,
        *,
        model_backend: str,
        prompt: str,
        files: list[dict[str, object]],
    ) -> str:
        if "OUTPUT FORMAT SAMPLE" in prompt:
            file_name = str(files[0]["filename"])
            stem = Path(file_name).stem
            return (
                '{"knowledges": ['
                f'{{"name": "Conceito {stem}", "description": "Descricao de {stem}", "files": ["{file_name}"]}}'
                "]}"
            )
        return f"# Conhecimento\n\nGerado a partir de {files[0]['filename']}\n"

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        if "OUTPUT FORMAT SAMPLE" in prompt:
            return (
                '{"knowledges": ['
                '{"name": "Conceito texto", "description": "Descricao de texto", "files": ["a.txt"]}'
                "]}"
            )
        return "# Conhecimento\n\nGerado a partir de texto inline\n"


def _patch_settings(monkeypatch, tmp_path: Path) -> None:
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


def test_pipeline_command_processes_directory(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    db_path = tmp_path / "pipeline.db"
    input_dir.mkdir()
    (input_dir / "a.pdf").write_bytes(b"%PDF-1.4\n")
    (input_dir / "b.txt").write_text("conteudo", encoding="utf-8")
    _patch_settings(monkeypatch, tmp_path)
    monkeypatch.setattr(
        cli_module, "create_client", lambda settings: DummyPipelineClient()
    )

    result = runner.invoke(
        app,
        [
            "pipeline",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--db-path",
            str(db_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Pipeline concluído" in result.stdout
    assert any((output_dir / "indexes").glob("*.json"))
    assert any((output_dir / "docs_livros").glob("*.md"))
    assert db_path.exists()


def test_pipeline_command_honors_environment_db_path(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    env_db_path = tmp_path / "env-pipeline.db"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("conteudo", encoding="utf-8")
    _patch_settings(monkeypatch, tmp_path)
    monkeypatch.setenv("ADAPTA_PIPELINE_DB_PATH", str(env_db_path))
    monkeypatch.setattr(
        cli_module, "create_client", lambda settings: DummyPipelineClient()
    )

    result = runner.invoke(
        app,
        [
            "pipeline",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert env_db_path.exists()


def test_pipeline_command_uses_inline_txt_without_upload(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    client = DummyPipelineClient()
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("conteudo inline", encoding="utf-8")
    _patch_settings(monkeypatch, tmp_path)
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "pipeline",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert client.uploaded == []
