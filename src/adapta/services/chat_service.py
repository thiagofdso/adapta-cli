from __future__ import annotations

import secrets
import time
import uuid

from adapta.models import ChatSession


def generate_chat_id() -> str:
    uuid7_factory = getattr(uuid, "uuid7", None)
    if callable(uuid7_factory):
        return str(uuid7_factory())

    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = secrets.randbits(12)
    rand_b = secrets.randbits(62)
    uuid_int = (
        (timestamp_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    )
    return str(uuid.UUID(int=uuid_int))


def create_chat_session(
    model_key: str, chat_id_factory=generate_chat_id
) -> ChatSession:
    return ChatSession(
        chat_id=chat_id_factory(), model_key=model_key, cleanup_required=False
    )


async def send_chat_message(
    client, session: ChatSession, model_backend: str, prompt_text: str
) -> str:
    session.messages.append({"role": "user", "content": prompt_text})
    response = await client.chat(
        model_backend=model_backend, messages=session.messages, chat_id=session.chat_id
    )
    session.messages.append({"role": "assistant", "content": response})
    session.cleanup_required = True
    return response


async def close_chat_session(client, session: ChatSession) -> None:
    if session.cleanup_required:
        await client.delete_chat(session.chat_id)
