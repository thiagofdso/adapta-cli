from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import adapta.cli as cli_module
from adapta.cli import app
from adapta.config import Settings


class DummySkillClient:
    def __init__(self) -> None:
        self.uploaded: list[Path] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        self.uploaded.append(file_path)
        return {"path": f"uploads/{file_path.name}"}

    async def prompt(self, *, model_backend: str, prompt: str, keep_chat: bool = True) -> str:
        if "OUTPUT FORMAT SAMPLE" in prompt:
            return (
                '{"skills": ['
                '{"name": "Metodo Texto", "description": "Descricao de texto", '
                '"files": [{"name": "aula.txt", "contribution": "Apresenta a pratica"}]}'
                "]}"
            )
        return (
            "---\n"
            "name: metodo-texto\n"
            "description: >\n"
            "  Gera uma skill textual. Use quando houver material de curso.\n"
            "---\n\n"
            "# Metodo Texto\n\n"
            "## 🎯 Categoria\n"
            "Metodo\n\n"
            "## 📌 Descricao\n"
            "Aplique o metodo.\n\n"
            "## 📝 Instrucoes\n"
            "Execute as etapas.\n\n"
            "## ⚡ Passo a Passo\n"
            "1. Execute.\n\n"
            "## 💡 Exemplos de Aplicacao\n"
            "Use em um curso.\n\n"
            "## ⚠️ Pontos de Atencao\n"
            "Nao se aplica\n\n"
            "## 🔧 Recursos Necessarios\n"
            "Material textual.\n\n"
            "## Consideracoes\n"
            "Nao se aplica\n"
        )


def _patch_settings(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        cli_module,
        "load_settings",
        lambda env_file=None: Settings(
            adapta_login="user@example.com",
            adapta_password="secret",
            adapta_model=None,
            env_file_path=tmp_path / ".env",
            data_dir=tmp_path / "data",
        ),
    )


def test_skill_create_command_processes_directory(monkeypatch, tmp_path: Path) -> None:
    runner = CliRunner()
    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    db_path = tmp_path / "skill-create.db"
    input_dir.mkdir()
    (input_dir / "aula.txt").write_text("conteudo", encoding="utf-8")
    (input_dir / "roteiro.md").write_text("conteudo", encoding="utf-8")
    _patch_settings(monkeypatch, tmp_path)
    client = DummySkillClient()
    monkeypatch.setattr(cli_module, "create_client", lambda settings: client)

    result = runner.invoke(
        app,
        [
            "skill-create",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--db-path",
            str(db_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Skill-create concluído" in result.stdout
    assert any((output_dir / "indexes").glob("*.json"))
    assert any((output_dir / "skills_curso").glob("*/SKILL.md"))
    assert db_path.exists()
    assert client.uploaded == []


def test_skill_create_command_honors_environment_db_path(
    monkeypatch, tmp_path: Path
) -> None:
    runner = CliRunner()
    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    env_db_path = tmp_path / "env-skill-create.db"
    input_dir.mkdir()
    (input_dir / "aula.txt").write_text("conteudo", encoding="utf-8")
    _patch_settings(monkeypatch, tmp_path)
    monkeypatch.setenv("ADAPTA_SKILL_CREATE_DB_PATH", str(env_db_path))
    monkeypatch.setattr(cli_module, "create_client", lambda settings: DummySkillClient())

    result = runner.invoke(
        app,
        [
            "skill-create",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert env_db_path.exists()
