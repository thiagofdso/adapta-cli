from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest

from adapta.services.skill_service import (
    build_skill_create_request,
    discover_skill_documents,
    run_skill_create,
    _merge_skill_entries,
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
