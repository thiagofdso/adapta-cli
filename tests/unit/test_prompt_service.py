from pathlib import Path

import pytest

from adapta.models import PromptRequest
from adapta.services.prompt_service import build_prompt_request, execute_prompt


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, list[str] | None]] = []
        self.deleted_chats: list[str] = []

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        self.calls.append((model_backend, prompt, None))
        return "2"

    async def prompt_ephemeral(self, *, model_backend: str, prompt: str) -> str:
        self.calls.append((model_backend, prompt, None))
        self.deleted_chats.append("ephemeral")
        return "2"

    async def prompt_with_files(
        self,
        *,
        model_backend: str,
        prompt: str,
        files: list[dict[str, object]],
    ) -> str:
        self.calls.append(
            (model_backend, prompt, [str(file["filename"]) for file in files])
        )
        return "2"

    async def prompt_with_files_ephemeral(
        self,
        *,
        model_backend: str,
        prompt: str,
        files: list[dict[str, object]],
    ) -> str:
        self.calls.append(
            (model_backend, prompt, [str(file["filename"]) for file in files])
        )
        self.deleted_chats.append("ephemeral")
        return "2"


def test_build_prompt_request_from_inline_text() -> None:
    request = build_prompt_request(
        model_key="gpt",
        prompt="olá",
        prompt_file=None,
        output=None,
        files=None,
    )

    assert isinstance(request, PromptRequest)
    assert request.prompt_text == "olá"
    assert request.prompt_source == "inline"
    assert request.file_paths == []


def test_build_prompt_request_from_file(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    attachment = tmp_path / "anexo.pdf"
    prompt_file.write_text("oi", encoding="utf-8")
    attachment.write_bytes(b"%PDF-1.4\n")

    request = build_prompt_request(
        model_key="gpt",
        prompt=None,
        prompt_file=prompt_file,
        output=tmp_path / "saida.txt",
        files=[attachment],
    )

    assert request.prompt_text == "oi"
    assert request.prompt_source == "file"
    assert request.output_path == tmp_path / "saida.txt"
    assert request.file_paths == [attachment]


def test_build_prompt_request_rejects_multiple_sources(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("oi", encoding="utf-8")

    with pytest.raises(ValueError):
        build_prompt_request("gpt", "oi", prompt_file, None, None)


def test_build_prompt_request_rejects_missing_sources() -> None:
    with pytest.raises(ValueError):
        build_prompt_request("gpt", None, None, None, None)


def test_build_prompt_request_rejects_empty_file(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("   ", encoding="utf-8")

    with pytest.raises(ValueError):
        build_prompt_request("gpt", None, prompt_file, None, None)


def test_build_prompt_request_rejects_more_than_five_files(tmp_path: Path) -> None:
    files = [tmp_path / f"anexo-{index}.pdf" for index in range(6)]

    with pytest.raises(ValueError, match="entre 1 e 5 arquivos"):
        build_prompt_request("gpt", "oi", None, None, files)


def test_build_prompt_request_rejects_missing_attachment_file(tmp_path: Path) -> None:
    missing = tmp_path / "inexistente.pdf"

    with pytest.raises(ValueError, match="Arquivo não encontrado"):
        build_prompt_request("gpt", "oi", None, None, [missing])


@pytest.mark.anyio
async def test_execute_prompt_calls_client() -> None:
    client = DummyClient()
    request = PromptRequest(
        model_key="gpt",
        prompt_text="quanto é 1+1 responda somente o valor",
        prompt_source="inline",
        output_path=None,
        file_paths=[],
    )

    response = await execute_prompt(client, request, model_backend="GPT_5")

    assert response.text == "2"
    assert client.calls == [("GPT_5", "quanto é 1+1 responda somente o valor", None)]
    assert client.deleted_chats == ["ephemeral"]


@pytest.mark.anyio
async def test_execute_prompt_calls_client_with_uploaded_files(tmp_path: Path) -> None:
    client = DummyClient()
    attachment = tmp_path / "anexo.pdf"
    attachment.write_bytes(b"%PDF-1.4\n")
    request = PromptRequest(
        model_key="gpt",
        prompt_text="resuma o anexo",
        prompt_source="inline",
        output_path=None,
        file_paths=[attachment],
    )

    async def upload_file(file_path: Path) -> dict[str, object]:
        return {
            "filename": file_path.name,
            "url": f"https://files.example/{file_path.name}",
            "size": 10,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    client.upload_file = upload_file  # type: ignore[attr-defined]

    response = await execute_prompt(client, request, model_backend="GPT_5")

    assert response.text == "2"
    assert client.calls == [("GPT_5", "resuma o anexo", ["anexo.pdf"])]
    assert client.deleted_chats == ["ephemeral"]
