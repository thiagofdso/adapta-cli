from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from adapta.services.pipeline_service import (
    build_pipeline_request,
    discover_pipeline_documents,
    run_pipeline,
)


class DummyPipelineClient:
    def __init__(self) -> None:
        self.deleted_files: list[str] = []
        self.deleted_chats: list[str] = []
        self.prompts: list[str] = []
        self.uploaded: list[Path] = []

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
        self.deleted_files.append(file_path)

    async def prompt_with_files(
        self,
        *,
        model_backend: str,
        prompt: str,
        files: list[dict[str, object]],
    ) -> str:
        self.prompts.append(prompt)
        if "OUTPUT FORMAT SAMPLE" in prompt:
            file_name = str(files[0]["filename"])
            stem = Path(file_name).stem
            return (
                '{"knowledges": ['
                f'{{"name": "Conceito {stem}", "description": "Descricao de {stem}", "files": ["{file_name}"]}}'
                "]}"
            )
        return f"# Conhecimento\n\nGerado a partir de {files[0]['filename']}\n"

    async def prompt_with_files_ephemeral(
        self,
        *,
        model_backend: str,
        prompt: str,
        files: list[dict[str, object]],
    ) -> str:
        self.deleted_chats.append("ephemeral-with-files")
        return await self.prompt_with_files(
            model_backend=model_backend,
            prompt=prompt,
            files=files,
        )

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        self.prompts.append(prompt)
        if "OUTPUT FORMAT SAMPLE" in prompt:
            return (
                '{"knowledges": ['
                '{"name": "Conceito texto", "description": "Descricao de texto", "files": ["livro.txt"]}'
                "]}"
            )
        return "# Conhecimento\n\nGerado a partir de texto inline\n"

    async def prompt_ephemeral(self, *, model_backend: str, prompt: str) -> str:
        self.deleted_chats.append("ephemeral")
        return await self.prompt(model_backend=model_backend, prompt=prompt)


def test_build_pipeline_request_rejects_missing_directories(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Informe --input-dir e --output-dir"):
        build_pipeline_request(
            input_dir=None,
            output_dir=tmp_path / "saida",
            db_path=None,
            mode="upload",
            job=None,
            keep_chat=False,
            log=False,
        )


def test_discover_pipeline_documents_scans_recursively(tmp_path: Path) -> None:
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    nested_dir = input_dir / "modulo"
    nested_dir.mkdir(parents=True)
    (input_dir / "a.pdf").write_bytes(b"%PDF-1.4\n")
    (nested_dir / "b.txt").write_text("conteudo", encoding="utf-8")
    (nested_dir / "ignorar.md").write_text("x", encoding="utf-8")

    request = build_pipeline_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=tmp_path / "pipeline.db",
        mode="upload",
        job=None,
        keep_chat=False,
        log=False,
    )

    documents = discover_pipeline_documents(request)

    assert [document.relative_path for document in documents] == [
        "a.pdf",
        "modulo/b.txt",
    ]


@pytest.mark.anyio
async def test_run_pipeline_writes_indexes_docs_and_database(tmp_path: Path) -> None:
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "a.pdf").write_bytes(b"%PDF-1.4\n")
    (input_dir / "b.txt").write_text("conteudo", encoding="utf-8")
    db_path = tmp_path / "pipeline.db"

    request = build_pipeline_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=db_path,
        mode="upload",
        job=None,
        keep_chat=False,
        log=False,
    )
    client = DummyPipelineClient()

    result = await run_pipeline(client, request)

    assert result.index_paths
    assert result.generated_documents
    assert all(path.exists() for path in result.index_paths)
    assert all(path.exists() for path in result.generated_documents)
    assert db_path.exists()
    connection = sqlite3.connect(str(db_path))
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    assert int(cursor.fetchone()[0]) == 2
    cursor.execute("SELECT COUNT(*) FROM knowledges")
    assert int(cursor.fetchone()[0]) >= 2
    connection.close()
    assert client.deleted_files == ["uploads/a.pdf", "uploads/a.pdf"]
    assert client.deleted_chats


@pytest.mark.anyio
async def test_run_pipeline_reports_empty_input_dir(tmp_path: Path) -> None:
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()

    request = build_pipeline_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=tmp_path / "pipeline.db",
        mode="upload",
        job=None,
        keep_chat=False,
        log=False,
    )

    with pytest.raises(ValueError, match="Nenhum arquivo compatível"):
        await run_pipeline(DummyPipelineClient(), request)


@pytest.mark.anyio
async def test_run_pipeline_inlines_txt_without_upload(tmp_path: Path) -> None:
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "livro.txt").write_text("conteudo inline", encoding="utf-8")
    db_path = tmp_path / "pipeline.db"

    request = build_pipeline_request(
        input_dir=input_dir,
        output_dir=output_dir,
        db_path=db_path,
        mode="upload",
        job=None,
        keep_chat=False,
        log=False,
    )
    client = DummyPipelineClient()

    result = await run_pipeline(client, request)

    assert result.generated_documents
    assert client.uploaded == []
    assert client.deleted_files == []
    assert client.deleted_chats
    assert any("ARQUIVOS TXT INLINE" in prompt for prompt in client.prompts)
