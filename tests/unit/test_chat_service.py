import pytest

from adapta.services.chat_service import (
    close_chat_session,
    create_chat_session,
    send_chat_message,
)


class DummyChatClient:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.messages = []

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        self.messages.append((model_backend, chat_id, list(messages), None))
        return "2"

    async def chat_with_files(
        self,
        *,
        model_backend: str,
        messages: list[dict[str, str]],
        chat_id: str,
        files: list[dict[str, object]],
    ) -> str:
        self.messages.append(
            (
                model_backend,
                chat_id,
                list(messages),
                [str(file["filename"]) for file in files],
            )
        )
        return "2"

    async def delete_chat(self, chat_id: str) -> None:
        self.deleted.append(chat_id)


@pytest.mark.anyio
async def test_chat_session_accumulates_messages() -> None:
    client = DummyChatClient()
    session = create_chat_session(model_key="gpt", chat_id_factory=lambda: "chat-1")

    response = await send_chat_message(
        client, session, model_backend="GPT_5", prompt_text="quanto é 1+1"
    )

    assert response == "2"
    assert session.chat_id == "chat-1"
    assert session.messages == [
        {"role": "user", "content": "quanto é 1+1"},
        {"role": "assistant", "content": "2"},
    ]
    assert client.messages == [
        (
            "GPT_5",
            "chat-1",
            [{"role": "user", "content": "quanto é 1+1"}],
            None,
        )
    ]


@pytest.mark.anyio
async def test_chat_session_uploads_files_when_provided(tmp_path) -> None:
    client = DummyChatClient()
    attachment = tmp_path / "anexo.pdf"
    attachment.write_bytes(b"%PDF-1.4\n")
    uploaded: list[str] = []

    async def upload_file(file_path):
        uploaded.append(file_path.name)
        return {
            "filename": file_path.name,
            "url": f"https://files.example/{file_path.name}",
            "size": 10,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    client.upload_file = upload_file  # type: ignore[attr-defined]
    session = create_chat_session(model_key="gpt", chat_id_factory=lambda: "chat-1")

    response = await send_chat_message(
        client,
        session,
        model_backend="GPT_5",
        prompt_text="analise o anexo",
        file_paths=[attachment],
    )

    assert response == "2"
    assert uploaded == ["anexo.pdf"]
    assert client.messages == [
        (
            "GPT_5",
            "chat-1",
            [{"role": "user", "content": "analise o anexo"}],
            ["anexo.pdf"],
        )
    ]


@pytest.mark.anyio
async def test_close_chat_session_deletes_remote_chat() -> None:
    client = DummyChatClient()
    session = create_chat_session(model_key="gpt", chat_id_factory=lambda: "chat-1")
    session.cleanup_required = True

    await close_chat_session(client, session)

    assert client.deleted == ["chat-1"]
