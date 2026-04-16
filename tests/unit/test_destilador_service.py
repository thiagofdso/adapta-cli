from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from adapta.services.destilador_service import (
    build_distillation_request,
    distill_documents,
    resolve_distillation_items,
)


class DummyDistillationClient:
    def __init__(self) -> None:
        self.uploaded: list[Path] = []
        self.deleted_files: list[str] = []
        self.deleted_chats: list[str | list[str]] = []
        self.calls: list[tuple[str, str]] = []

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        self.uploaded.append(file_path)
        return {
            "filename": file_path.name,
            "url": f"https://example.invalid/{file_path.name}",
            "size": 10,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    async def delete_file(self, file_path: str) -> None:
        self.deleted_files.append(file_path)

    async def delete_chat(self, chat_id: str | list[str]) -> None:
        self.deleted_chats.append(chat_id)

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, object]], chat_id: str
    ) -> str:
        self.calls.append((model_backend, chat_id))
        dimension_text = str(messages[0]["content"][0]["text"])
        if "DIMENSÃO 1" in dimension_text:
            return (
                "resposta curta" if len(self.calls) % 2 else "resposta longa dimensão 1"
            )
        return f"conteudo {len(self.calls)}"


def test_build_distillation_request_rejects_mixed_modes(tmp_path: Path) -> None:
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    with pytest.raises(ValueError, match="Use apenas um modo"):
        build_distillation_request(
            input_path=pdf_path,
            input_dir=tmp_path,
            output_path=tmp_path / "saida.md",
            output_dir=tmp_path / "saidas",
        )


def test_resolve_distillation_items_for_single_file(tmp_path: Path) -> None:
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    request = build_distillation_request(
        input_path=pdf_path,
        input_dir=None,
        output_path=tmp_path / "saida.md",
        output_dir=None,
    )

    items = resolve_distillation_items(request)

    assert len(items) == 1
    assert items[0].source_path == pdf_path
    assert items[0].target_output_path == tmp_path / "saida.md"


def test_resolve_distillation_items_for_single_file_with_output_dir(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "livro.pdf"
    output_dir = tmp_path / "saidas"
    pdf_path.write_bytes(b"%PDF-1.4\n")

    request = build_distillation_request(
        input_path=pdf_path,
        input_dir=None,
        output_path=None,
        output_dir=output_dir,
    )

    items = resolve_distillation_items(request)

    assert len(items) == 1
    assert items[0].source_path == pdf_path
    assert items[0].target_output_path == output_dir / "livro.md"


def test_resolve_distillation_items_for_directory(tmp_path: Path) -> None:
    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saidas"
    input_dir.mkdir()
    output_dir.mkdir()
    (input_dir / "a.pdf").write_bytes(b"%PDF-1.4\n")
    (input_dir / "b.pdf").write_bytes(b"%PDF-1.4\n")
    (input_dir / "c.txt").write_text("x", encoding="utf-8")

    request = build_distillation_request(
        input_path=None,
        input_dir=input_dir,
        output_path=None,
        output_dir=output_dir,
    )

    items = resolve_distillation_items(request)

    assert [item.source_path.name for item in items] == ["a.pdf", "b.pdf", "c.txt"]
    assert [item.target_output_path.name for item in items] == ["a.md", "b.md", "c.md"]


@pytest.mark.anyio
async def test_distill_documents_writes_output_and_cleans_remote_file(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "livro.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    request = build_distillation_request(
        input_path=pdf_path,
        input_dir=None,
        output_path=tmp_path / "saida.md",
        output_dir=None,
    )
    client = DummyDistillationClient()

    result = await distill_documents(client, request)

    output_text = (tmp_path / "saida.md").read_text(encoding="utf-8")
    assert result.final_output_paths == [tmp_path / "saida.md"]
    assert "resposta longa dimensão 1" in output_text
    assert client.deleted_files == ["uploads/livro.pdf"]
    assert client.deleted_chats


@pytest.mark.anyio
async def test_distill_documents_preserves_partials_when_output_dir_used(
    tmp_path: Path,
) -> None:
    pdf_path = tmp_path / "livro.pdf"
    output_dir = tmp_path / "saidas"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    request = build_distillation_request(
        input_path=pdf_path,
        input_dir=None,
        output_path=None,
        output_dir=output_dir,
    )
    client = DummyDistillationClient()

    result = await distill_documents(client, request)

    assert result.final_output_paths == [output_dir / "livro.md"]
    assert (output_dir / "livro" / "dimensao1.txt").exists()
    assert (output_dir / "livro" / "dimensao7.txt").exists()
    assert client.deleted_chats


@pytest.mark.anyio
async def test_distill_documents_inlines_txt_without_upload(tmp_path: Path) -> None:
    txt_path = tmp_path / "livro.txt"
    txt_path.write_text("conteudo do livro em texto", encoding="utf-8")
    request = build_distillation_request(
        input_path=txt_path,
        input_dir=None,
        output_path=tmp_path / "saida.md",
        output_dir=None,
    )
    client = DummyDistillationClient()

    result = await distill_documents(client, request)

    assert result.final_output_paths == [tmp_path / "saida.md"]
    assert client.uploaded == []
    assert client.deleted_files == []
    assert client.deleted_chats


@pytest.mark.anyio
async def test_distill_documents_processes_items_in_parallel(
    monkeypatch, tmp_path: Path
) -> None:
    class ParallelDistillationClient(DummyDistillationClient):
        def __init__(self) -> None:
            super().__init__()
            self.in_flight = 0
            self.max_in_flight = 0
            self.release_event = asyncio.Event()

        async def chat(
            self, *, model_backend: str, messages: list[dict[str, object]], chat_id: str
        ) -> str:
            self.calls.append((model_backend, chat_id))
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
            if self.in_flight >= 2:
                self.release_event.set()
            await asyncio.wait_for(self.release_event.wait(), timeout=1)
            self.in_flight -= 1
            return "conteudo paralelo"

    input_dir = tmp_path / "livros"
    output_dir = tmp_path / "saida"
    input_dir.mkdir()
    (input_dir / "a.txt").write_text("conteudo A", encoding="utf-8")
    (input_dir / "b.txt").write_text("conteudo B", encoding="utf-8")
    request = build_distillation_request(
        input_path=None,
        input_dir=input_dir,
        output_path=None,
        output_dir=output_dir,
    )
    client = ParallelDistillationClient()
    monkeypatch.setattr(
        "adapta.services.destilador_service.DISTILLATION_ITERATIONS", 1
    )
    monkeypatch.setattr(
        "adapta.services.destilador_service.DISTILLATION_RETRY_LIMIT", 1
    )

    await distill_documents(client, request)

    assert client.max_in_flight >= 2
