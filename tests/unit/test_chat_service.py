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
        self.messages.append((model_backend, chat_id, list(messages)))
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


@pytest.mark.anyio
async def test_close_chat_session_deletes_remote_chat() -> None:
    client = DummyChatClient()
    session = create_chat_session(model_key="gpt", chat_id_factory=lambda: "chat-1")
    session.cleanup_required = True

    await close_chat_session(client, session)

    assert client.deleted == ["chat-1"]
