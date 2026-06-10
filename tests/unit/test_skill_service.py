from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path

import pytest

from adapta.services.skill_service import (
    build_skill_create_request,
    discover_skill_documents,
    run_skill_create,
    _load_index_data,
    _merge_skill_entries,
    _upsert_skills,
    _validate_skill_entries,
    _validate_skill_markdown,
)


class DummySkillClient:
    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.uploaded: list[Path] = []

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        self.uploaded.append(file_path)
        return {"path": f"uploads/{file_path.name}"}

    async def prompt(self, *, model_backend: str, prompt: str, keep_chat: bool = True) -> str:
        self.prompts.append(prompt)
        if "OUTPUT FORMAT SAMPLE" in prompt:
            return (
                '{"skills": ['
                '{"name": "Metodo texto", "description": "Descricao de texto", '
                '"files": [{"name": "aula.txt", "contribution": "Apresenta a pratica"}]}'
                "]}"
            )
        return VALID_SKILL_MARKDOWN


VALID_SKILL_MARKDOWN = (
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


def test_build_skill_create_request_rejects_missing_directories(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Informe --input-dir e --output-dir"):
        build_skill_create_request(
            input_dir=None,
            output_dir=tmp_path / "saida",
            db_path=None,
            job=None,
            keep_chat=False,
            log=False,
        )


def test_discover_skill_documents_scans_text_and_markdown(tmp_path: Path) -> None:
    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    nested_dir = input_dir / "modulo"
    nested_dir.mkdir(parents=True)
    (input_dir / "aula.txt").write_text("conteudo", encoding="utf-8")
    (nested_dir / "roteiro.md").write_text("conteudo", encoding="utf-8")
    (nested_dir / "ignorar.pdf").write_bytes(b"%PDF-1.4\n")

    request = build_skill_create_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=tmp_path / "skill-create.db",
        job=None,
        keep_chat=False,
        log=False,
    )

    documents = discover_skill_documents(request)

    assert [document.relative_path for document in documents] == [
        "aula.txt",
        "modulo/roteiro.md",
    ]


def test_merge_skill_entries_patches_by_id_and_accumulates_files() -> None:
    existing = [
        {
            "id": "metodo-persona",
            "name": "Metodo Persona",
            "description": "Descricao antiga",
            "files": [{"name": "aula01.txt", "contribution": "Base"}],
        }
    ]
    new = [
        {
            "id": "metodo-persona",
            "name": "Metodo Persona Atualizado",
            "description": "Descricao atualizada",
            "files": [{"name": "aula02.txt", "contribution": "Exemplo pratico"}],
        }
    ]

    merged = _merge_skill_entries(existing, new)

    assert len(merged) == 1
    assert merged[0]["id"] == "metodo-persona"
    assert merged[0]["name"] == "Metodo Persona"
    assert merged[0]["description"] == "Descricao atualizada"
    assert merged[0]["files"] == [
        {"name": "aula01.txt", "contribution": "Base"},
        {"name": "aula02.txt", "contribution": "Exemplo pratico"},
    ]


def test_merge_skill_entries_patches_by_normalized_name_when_id_changes() -> None:
    existing = [
        {
            "id": "tecnica-upscale-imagens-pixel-cut",
            "name": "Tecnica de Upscale de Imagens com Pixel Cut",
            "description": "Descricao antiga",
            "files": [{"name": "aula39.txt", "contribution": "Base"}],
        }
    ]
    new = [
        {
            "id": "tecnica-upscale-imagens-pixelcut",
            "name": "Tecnica de Upscale de Imagens com Pixel Cut",
            "description": "Descricao atualizada",
            "files": [{"name": "aula68.txt", "contribution": "Nova pratica"}],
        }
    ]

    merged = _merge_skill_entries(existing, new)

    assert len(merged) == 1
    assert merged[0]["id"] == "tecnica-upscale-imagens-pixel-cut"
    assert merged[0]["name"] == "Tecnica de Upscale de Imagens com Pixel Cut"
    assert merged[0]["description"] == "Descricao atualizada"
    assert merged[0]["files"] == [
        {"name": "aula39.txt", "contribution": "Base"},
        {"name": "aula68.txt", "contribution": "Nova pratica"},
    ]


def test_validate_skill_entries_rejects_duplicate_normalized_names() -> None:
    entries = [
        {
            "id": "tecnica-upscale-imagens-pixel-cut",
            "name": "Tecnica de Upscale de Imagens com Pixel Cut",
            "description": "Descricao A",
            "files": [{"name": "aula39.txt", "contribution": "Base"}],
        },
        {
            "id": "tecnica-upscale-imagens-pixelcut",
            "name": "Técnica de Upscale de Imagens com Pixel Cut",
            "description": "Descricao B",
            "files": [{"name": "aula68.txt", "contribution": "Nova pratica"}],
        },
    ]

    with pytest.raises(RuntimeError, match="Nome de skill duplicado"):
        _validate_skill_entries(entries)


def test_load_index_data_repairs_legacy_duplicate_names(tmp_path: Path) -> None:
    index_path = tmp_path / "raw.json"
    index_path.write_text(
        json.dumps(
            {
                "skills": [
                    {
                        "id": "tecnica-upscale-imagens-pixel-cut",
                        "name": "Tecnica de Upscale de Imagens com Pixel Cut",
                        "description": "Descricao antiga",
                        "files": [{"name": "aula39.txt", "contribution": "Base"}],
                    },
                    {
                        "id": "tecnica-upscale-imagens-pixelcut",
                        "name": "Tecnica de Upscale de Imagens com Pixel Cut",
                        "description": "Descricao atualizada",
                        "files": [{"name": "aula68.txt", "contribution": "Nova pratica"}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    entries = _load_index_data(index_path)

    assert len(entries) == 1
    assert entries[0]["id"] == "tecnica-upscale-imagens-pixel-cut"
    assert entries[0]["description"] == "Descricao atualizada"
    assert entries[0]["files"] == [
        {"name": "aula39.txt", "contribution": "Base"},
        {"name": "aula68.txt", "contribution": "Nova pratica"},
    ]


def test_upsert_skills_updates_existing_row_when_name_matches_even_with_different_key() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_key TEXT,
            name TEXT NOT NULL,
            description TEXT,
            position INTEGER,
            folder_path TEXT NOT NULL,
            status_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, folder_path)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE files_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            contribution TEXT,
            UNIQUE(skill_id, file_name),
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
        """
    )
    folder_path = "/curso/raw"
    _upsert_skills(
        connection,
        folder_path,
        [
            {
                "id": "tecnica-upscale-imagens-pixel-cut",
                "name": "Tecnica de Upscale de Imagens com Pixel Cut",
                "description": "Descricao antiga",
                "files": [{"name": "aula39.txt", "contribution": "Base"}],
            }
        ],
    )

    _upsert_skills(
        connection,
        folder_path,
        [
            {
                "id": "tecnica-upscale-imagens-pixelcut",
                "name": "Tecnica de Upscale de Imagens com Pixel Cut",
                "description": "Descricao atualizada",
                "files": [{"name": "aula68.txt", "contribution": "Nova pratica"}],
            }
        ],
    )

    cursor.execute("SELECT skill_key, name, description FROM skills")
    rows = cursor.fetchall()
    assert len(rows) == 1
    assert rows[0]["skill_key"] == "tecnica-upscale-imagens-pixelcut"
    assert rows[0]["description"] == "Descricao atualizada"
    cursor.execute("SELECT file_name FROM files_skills")
    assert [row[0] for row in cursor.fetchall()] == ["aula68.txt"]
    connection.close()


def test_validate_skill_markdown_rejects_wrapped_commentary() -> None:
    invalid = f"Com base no material fornecido, aqui esta a SKILL.md:\n\n```markdown\n{VALID_SKILL_MARKDOWN}```"

    with pytest.raises(RuntimeError, match="comentários ou markdown fences"):
        _validate_skill_markdown(invalid)


def test_validate_skill_markdown_rejects_invalid_header() -> None:
    invalid = VALID_SKILL_MARKDOWN.replace("name: metodo-texto", "name: Metodo Texto")

    with pytest.raises(RuntimeError, match="name em hyphen-case"):
        _validate_skill_markdown(invalid)


def test_validate_skill_markdown_allows_code_fences_inside_body() -> None:
    valid = VALID_SKILL_MARKDOWN.replace(
        "Execute as etapas.",
        "Execute as etapas.\n\n```python\nprint('ok')\n```",
    )

    assert _validate_skill_markdown(valid) == valid


def test_validate_skill_markdown_allows_bracket_arguments_inside_body() -> None:
    valid = VALID_SKILL_MARKDOWN.replace(
        "Execute as etapas.",
        "Execute `uv add [nome-da-biblioteca]` quando precisar instalar pacotes.",
    )

    assert _validate_skill_markdown(valid) == valid


@pytest.mark.anyio
async def test_run_skill_create_repairs_invalid_skill_markdown_once(tmp_path: Path) -> None:
    class RepairingSkillClient(DummySkillClient):
        def __init__(self) -> None:
            super().__init__()
            self.chat_calls = 0

        async def chat(
            self,
            *,
            model_backend: str,
            messages: list[dict[str, str]],
            chat_id: str,
        ) -> str:
            self.chat_calls += 1
            if self.chat_calls == 1:
                return (
                    "Com base no material fornecido, aqui esta a SKILL.md:\n\n"
                    f"```markdown\n{VALID_SKILL_MARKDOWN}```"
                )
            return VALID_SKILL_MARKDOWN

        async def delete_chat(self, chat_id: str) -> None:
            return None

    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "aula.txt").write_text("conteudo inline", encoding="utf-8")
    request = build_skill_create_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=tmp_path / "skill-create.db",
        job=None,
        keep_chat=False,
        log=False,
    )
    client = RepairingSkillClient()

    result = await run_skill_create(client, request)

    assert client.chat_calls == 2
    assert result.generated_skills[0].read_text(encoding="utf-8") == VALID_SKILL_MARKDOWN


@pytest.mark.anyio
async def test_run_skill_create_stops_when_repair_stays_invalid(tmp_path: Path) -> None:
    class BrokenSkillClient(DummySkillClient):
        async def chat(
            self,
            *,
            model_backend: str,
            messages: list[dict[str, str]],
            chat_id: str,
        ) -> str:
            return "ChatCompletionResult(messages=[{'kind': 'answer', 'text': ''}])"

        async def delete_chat(self, chat_id: str) -> None:
            return None

    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "aula.txt").write_text("conteudo inline", encoding="utf-8")
    request = build_skill_create_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=tmp_path / "skill-create.db",
        job=None,
        keep_chat=False,
        log=False,
    )

    with pytest.raises(RuntimeError, match="Erro na geração de skill"):
        await run_skill_create(BrokenSkillClient(), request)


@pytest.mark.anyio
async def test_run_skill_create_writes_indexes_skill_dirs_and_database(tmp_path: Path) -> None:
    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "aula.txt").write_text("conteudo inline", encoding="utf-8")
    db_path = tmp_path / "skill-create.db"

    request = build_skill_create_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=db_path,
        job=None,
        keep_chat=False,
        log=False,
    )
    client = DummySkillClient()

    result = await run_skill_create(client, request)

    assert result.index_paths
    assert result.generated_skills
    assert all(path.exists() for path in result.index_paths)
    assert all(path.name == "SKILL.md" for path in result.generated_skills)
    assert all(path.exists() for path in result.generated_skills)
    assert client.uploaded == []
    assert any("ARQUIVOS INLINE" in prompt for prompt in client.prompts)
    connection = sqlite3.connect(str(db_path))
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    assert int(cursor.fetchone()[0]) == 1
    cursor.execute("SELECT COUNT(*) FROM skills")
    assert int(cursor.fetchone()[0]) == 1
    connection.close()


@pytest.mark.anyio
async def test_run_skill_create_reports_empty_input_dir(tmp_path: Path) -> None:
    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()

    request = build_skill_create_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=tmp_path / "skill-create.db",
        job=None,
        keep_chat=False,
        log=False,
    )

    with pytest.raises(ValueError, match="Nenhum arquivo compatível"):
        await run_skill_create(DummySkillClient(), request)


@pytest.mark.anyio
async def test_run_skill_create_does_not_regenerate_completed_skills(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "aula.txt").write_text("conteudo inline", encoding="utf-8")
    db_path = tmp_path / "skill-create.db"
    request = build_skill_create_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=db_path,
        job=None,
        keep_chat=False,
        log=False,
    )
    client = DummySkillClient()
    progress_messages: list[str] = []

    first_result = await run_skill_create(client, request)
    first_prompt_count = len(client.prompts)
    second_result = await run_skill_create(
        client,
        request,
        progress_callback=progress_messages.append,
    )

    assert first_result.generated_skills
    assert second_result.generated_skills == []
    assert len(client.prompts) == first_prompt_count
    connection = sqlite3.connect(str(db_path))
    cursor = connection.cursor()
    cursor.execute("SELECT status_id FROM skills")
    assert [int(row[0]) for row in cursor.fetchall()] == [3]
    connection.close()
    assert "Ignorando (já indexado): aula.txt" in progress_messages
    assert "Ignorando (já gerado): Metodo texto" in progress_messages


@pytest.mark.anyio
async def test_run_skill_create_generates_stage2_in_parallel(
    monkeypatch, tmp_path: Path
) -> None:
    class ParallelSkillClient(DummySkillClient):
        def __init__(self) -> None:
            super().__init__()
            self.in_flight = 0
            self.max_in_flight = 0
            self.release_event = asyncio.Event()

        async def prompt(self, *, model_backend: str, prompt: str, keep_chat: bool = True) -> str:
            self.prompts.append(prompt)
            if "OUTPUT FORMAT SAMPLE" in prompt:
                return (
                    '{"skills": ['
                    '{"name": "Metodo A", "description": "Descricao A", "files": [{"name": "aula.txt", "contribution": "Base"}]},'
                    '{"name": "Tecnica B", "description": "Descricao B", "files": [{"name": "aula.txt", "contribution": "Pratica"}]}'
                    "]}"
                )
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
            if self.in_flight >= 2:
                self.release_event.set()
            await asyncio.wait_for(self.release_event.wait(), timeout=1)
            self.in_flight -= 1
            return VALID_SKILL_MARKDOWN

    input_dir = tmp_path / "curso"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "aula.txt").write_text("conteudo inline", encoding="utf-8")
    request = build_skill_create_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=tmp_path / "skill-create.db",
        job=None,
        keep_chat=False,
        log=False,
    )
    client = ParallelSkillClient()
    monkeypatch.setattr("adapta.services.skill_service.SKILL_STAGE2_CONCURRENCY", 2)

    await run_skill_create(client, request)

    assert client.max_in_flight >= 2
