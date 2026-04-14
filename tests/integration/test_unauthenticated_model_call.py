from __future__ import annotations

import httpx
import pytest

from adapta.client import AGENT_BASE_URL, CLERK_JS_VERSION, CLERK_API_VERSION


@pytest.mark.anyio
async def test_model_call_without_login_returns_auth_error() -> None:
    payload = {
        "mandatoryTools": [],
        "chatId": "unauthenticated-test-chat",
        "contextsIds": [],
        "meetingContextsIds": [],
        "modelAi": "CLAUDE_4_5_SONNET",
        "id": "unauthenticated-test-chat",
        "messages": [
            {
                "id": "unauthenticated-test-message",
                "role": "user",
                "parts": [{"type": "text", "text": "responda apenas ok"}],
            }
        ],
        "trigger": "submit-message",
        "messageId": "unauthenticated-test-message",
    }
    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "origin": AGENT_BASE_URL,
        "referer": f"{AGENT_BASE_URL}/agentic-chat",
        "x-clerk-api-version": CLERK_API_VERSION,
        "x-clerk-js-version": CLERK_JS_VERSION,
    }

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.post(
            f"{AGENT_BASE_URL}/api/chat/stream/v1",
            headers=headers,
            json=payload,
        )

    assert response.status_code >= 400, (
        f"Esperava erro de autenticação, mas recebi {response.status_code}: "
        f"{response.text[:500]}"
    )
