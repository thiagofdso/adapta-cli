from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from adapta.client import (
    AGENT_BASE_URL,
    API_AGENT_BASE_URL,
    AdaptaAuthenticator,
    AdaptaClientAdapter,
    AdaptaConversationClient,
    AdaptaHttpSession,
    ChatCompletionResult,
    extract_answer_text,
    import_cookies_to_session_cache,
    should_logout,
)


class DummyAuthenticator:
    async def ensure_authenticated(self) -> None:
        return None

    async def ensure_bearer_token(self) -> str:
        return "test-token"


def _build_client(
    handler: httpx.MockTransport,
) -> tuple[AdaptaConversationClient, AdaptaHttpSession]:
    session = AdaptaHttpSession(transport=handler)
    client = AdaptaConversationClient(
        session=session,
        authenticator=DummyAuthenticator(),
    )
    return client, session


@pytest.mark.anyio
async def test_list_files_fetches_all_pages_and_normalizes_entries() -> None:
    requests: list[str] = []
    first_page = [
        {
            "fileName": f"arquivo-{index}.pdf",
            "signedUrl": f"https://files.example/arquivo-{index}.pdf",
            "fileSizeInBytes": index,
            "fileMimeType": "application/pdf",
            "filePathOnStorage": f"uploads/arquivo-{index}.pdf",
        }
        for index in range(20)
    ]
    second_page = [
        {
            "name": "b.pdf",
            "url": "https://files.example/b.pdf",
            "size": 12,
            "mediaType": "application/pdf",
            "path": "uploads/b.pdf",
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        assert request.headers["authorization"] == "Bearer test-token"
        assert request.method == "GET"

        if str(request.url) == f"{AGENT_BASE_URL}/api/files/v2?limit=20":
            return httpx.Response(
                200,
                json={"data": first_page},
            )

        if (
            str(request.url)
            == f"{AGENT_BASE_URL}/api/files/v2?limit=20&offset=20&skipStorage=true"
        ):
            return httpx.Response(
                200,
                json={"data": second_page},
            )

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client, session = _build_client(httpx.MockTransport(handler))

    try:
        files = await client.list_files()
    finally:
        await session.close()

    assert files[:2] == [
        {
            "filename": "arquivo-0.pdf",
            "url": "https://files.example/arquivo-0.pdf",
            "size": 0,
            "mediaType": "application/pdf",
            "path": "uploads/arquivo-0.pdf",
        },
        {
            "filename": "arquivo-1.pdf",
            "url": "https://files.example/arquivo-1.pdf",
            "size": 1,
            "mediaType": "application/pdf",
            "path": "uploads/arquivo-1.pdf",
        },
    ]
    assert files[-1] == {
        "filename": "b.pdf",
        "url": "https://files.example/b.pdf",
        "size": 12,
        "mediaType": "application/pdf",
        "path": "uploads/b.pdf",
    }
    assert len(files) == 21
    assert requests == [
        f"{AGENT_BASE_URL}/api/files/v2?limit=20",
        f"{AGENT_BASE_URL}/api/files/v2?limit=20&offset=20&skipStorage=true",
    ]


@pytest.mark.anyio
async def test_upload_file_reuses_existing_remote_file_without_new_upload(
    tmp_path: Path,
) -> None:
    source_file = tmp_path / "livro.pdf"
    source_file.write_bytes(b"%PDF-1.4\n")
    requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, str(request.url)))

        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "fileName": "livro.pdf",
                            "signedUrl": "https://files.example/livro.pdf",
                            "fileSizeInBytes": len(source_file.read_bytes()),
                            "fileMimeType": "application/pdf",
                            "filePathOnStorage": "uploads/livro.pdf",
                        }
                    ]
                },
            )

        if (
            request.method == "POST"
            and str(request.url) == f"{API_AGENT_BASE_URL}/api/file/upload"
        ):
            raise AssertionError("upload should be skipped when file already exists")

        raise AssertionError(f"Unexpected request: {request.method} {request.url}")

    client, session = _build_client(httpx.MockTransport(handler))

    try:
        upload_info = await client.upload_file(source_file)
    finally:
        await session.close()

    assert upload_info == {
        "filename": "livro.pdf",
        "url": "https://files.example/livro.pdf",
        "size": len(source_file.read_bytes()),
        "mediaType": "application/pdf",
        "path": "uploads/livro.pdf",
    }
    assert requests == [
        ("GET", f"{AGENT_BASE_URL}/api/files/v2?limit=20"),
    ]


@pytest.mark.anyio
async def test_authenticator_restores_cached_session_from_disk(tmp_path: Path) -> None:
    cache_path = tmp_path / "cookies.json"
    cache_path.write_text(
        '{"session_id": "sess_123", "cookies": {"__session": "cookie-123"}, '
        '"bearer_token": "token-123", "bearer_token_exp": 9999999999, '
        '"used_production_token": true, "headers": {"authorization": "Bearer token-123"}}',
        encoding="utf-8",
    )

    session = AdaptaHttpSession()
    authenticator = AdaptaAuthenticator(
        session=session,
        login="user@example.com",
        password="secret",
        session_cache_path=cache_path,
    )

    client = await session.ensure_client()
    try:
        assert authenticator.session_id == "sess_123"
        assert client.cookies.get("__session") == "cookie-123"
        assert await authenticator.ensure_bearer_token() == "token-123"
    finally:
        await session.close()


@pytest.mark.anyio
async def test_ensure_authenticated_uses_cached_session_before_login(
    tmp_path: Path,
) -> None:
    cache_path = tmp_path / "cookies.json"
    cache_path.write_text(
        '{"session_id": "sess_cached", "cookies": {"__session": "cookie-cached"}}',
        encoding="utf-8",
    )
    session = AdaptaHttpSession()
    authenticator = AdaptaAuthenticator(
        session=session,
        login="user@example.com",
        password="secret",
        session_cache_path=cache_path,
    )
    touched: list[str] = []

    async def fake_touch(client, session_id: str, *, intent: str | None = None) -> None:
        touched.append(session_id)

    async def fail_login() -> None:
        raise AssertionError("login não deveria ser executado com cache válido")

    authenticator._touch_session = fake_touch  # type: ignore[method-assign]
    authenticator.simulate_login = fail_login  # type: ignore[method-assign]

    try:
        await authenticator.ensure_authenticated()
    finally:
        await session.close()

    assert touched == ["sess_cached"]


@pytest.mark.anyio
async def test_ensure_authenticated_regenerates_cache_on_401(tmp_path: Path) -> None:
    cache_path = tmp_path / "cookies.json"
    cache_path.write_text(
        '{"session_id": "sess_old", "cookies": {"__session": "cookie-old"}}',
        encoding="utf-8",
    )
    session = AdaptaHttpSession()
    authenticator = AdaptaAuthenticator(
        session=session,
        login="user@example.com",
        password="secret",
        session_cache_path=cache_path,
    )
    request = httpx.Request("POST", f"{AGENT_BASE_URL}/touch")
    state = {"raised": False}

    async def fake_touch(client, session_id: str, *, intent: str | None = None) -> None:
        if not state["raised"]:
            state["raised"] = True
            raise httpx.HTTPStatusError(
                "401", request=request, response=httpx.Response(401, request=request)
            )

    async def fake_login():
        authenticator._session_id = "sess_new"
        authenticator._session.remember_cookies({"__session": "cookie-new"})
        authenticator._persist_session_state()

    authenticator._touch_session = fake_touch  # type: ignore[method-assign]
    authenticator.simulate_login = fake_login  # type: ignore[method-assign]

    try:
        await authenticator.ensure_authenticated()
    finally:
        await session.close()

    payload = cache_path.read_text(encoding="utf-8")
    assert '"sess_new"' in payload
    assert '"cookie-new"' in payload


@pytest.mark.anyio
async def test_call_model_retries_after_401() -> None:
    class RetryAuthenticator:
        def __init__(self) -> None:
            self.reset_calls = 0

        async def ensure_authenticated(self) -> None:
            return None

        async def ensure_bearer_token(self) -> str:
            return "token-new" if self.reset_calls else "token-old"

        async def reset_authentication(self, *, drop_cache: bool) -> None:
            self.reset_calls += 1

    def handler(request: httpx.Request) -> httpx.Response:
        authorization = request.headers.get("authorization")
        if authorization == "Bearer token-old":
            return httpx.Response(401, request=request, json={"message": "expired"})
        if authorization == "Bearer token-new":
            return httpx.Response(
                200,
                request=request,
                text='data: {"type":"text-delta","delta":"ok"}\n\n'
                'data: {"type":"text-end"}\n\n'
                "data: [DONE]\n\n",
            )
        raise AssertionError(f"Unexpected authorization header: {authorization}")

    session = AdaptaHttpSession(transport=httpx.MockTransport(handler))
    client = AdaptaConversationClient(
        session=session,
        authenticator=RetryAuthenticator(),
    )

    try:
        result = await client.call_model(prompt="oi", model="GPT_5")
    finally:
        await session.close()

    assert result.messages == [{"kind": "answer", "text": "ok"}]


def test_should_logout_only_when_env_true(monkeypatch) -> None:
    monkeypatch.delenv("ADAPTA_LOGOUT", raising=False)
    assert should_logout() is False

    monkeypatch.setenv("ADAPTA_LOGOUT", "false")
    assert should_logout() is False

    monkeypatch.setenv("ADAPTA_LOGOUT", "true")
    assert should_logout() is True


def test_extract_answer_text_raises_for_empty_chat_completion_result() -> None:
    result = ChatCompletionResult(
        messages=[{"kind": "answer", "text": ""}],
        chat_id="chat-empty",
    )

    with pytest.raises(RuntimeError, match="texto vazio"):
        extract_answer_text(result)


@pytest.mark.anyio
async def test_call_model_reports_empty_stream_as_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            text='data: {"type":"text-end"}\n\n'
            "data: [DONE]\n\n",
        )

    client, session = _build_client(httpx.MockTransport(handler))

    try:
        result = await client.call_model(prompt="oi", model="GPT_5")
        with pytest.raises(RuntimeError, match="texto vazio"):
            extract_answer_text(result)
    finally:
        await session.close()


@pytest.mark.anyio
async def test_client_close_keeps_cached_session_when_logout_disabled(
    monkeypatch, tmp_path: Path
) -> None:
    cache_path = tmp_path / "cookies.json"
    cache_path.write_text(
        '{"session_id": "sess_123", "cookies": {"__session": "cookie-123"}}',
        encoding="utf-8",
    )
    monkeypatch.delenv("ADAPTA_LOGOUT", raising=False)

    adapter = AdaptaClientAdapter.__new__(AdaptaClientAdapter)
    adapter._session = AdaptaHttpSession()
    adapter._authenticator = AdaptaAuthenticator(
        session=adapter._session,
        login="user@example.com",
        password="secret",
        session_cache_path=cache_path,
    )

    await adapter.close()

    assert cache_path.exists()


@pytest.mark.anyio
async def test_client_close_removes_cached_session_when_logout_enabled(
    monkeypatch, tmp_path: Path
) -> None:
    cache_path = tmp_path / "cookies.json"
    cache_path.write_text(
        '{"session_id": "sess_123", "cookies": {"__session": "cookie-123"}}',
        encoding="utf-8",
    )
    monkeypatch.setenv("ADAPTA_LOGOUT", "true")

    adapter = AdaptaClientAdapter.__new__(AdaptaClientAdapter)
    adapter._session = AdaptaHttpSession()
    adapter._authenticator = AdaptaAuthenticator(
        session=adapter._session,
        login="user@example.com",
        password="secret",
        session_cache_path=cache_path,
    )

    await adapter.close()

    assert not cache_path.exists()


def test_import_cookies_to_session_cache_converts_browser_export(
    tmp_path: Path,
) -> None:
    source_path = tmp_path / "session.json"
    target_path = tmp_path / "cookies.json"
    source_path.write_text(
        """
[
  {"name": "clerk_active_context", "value": "sess_abc123:"},
  {"name": "__session", "value": "eyJhbGciOiJub25lIn0.eyJzaWQiOiJzZXNzX2FiYzEyMyJ9."},
  {"name": "__client_uat", "value": "1775593997"}
]
        """.strip(),
        encoding="utf-8",
    )

    destination, payload = import_cookies_to_session_cache(
        source_path, target_path=target_path
    )

    assert destination == target_path
    assert payload["session_id"] == "sess_abc123"
    assert payload["cookies"]["clerk_active_context"] == "sess_abc123:"
    assert payload["cookies"]["__client_uat"] == "1775593997"
    assert (
        json.loads(target_path.read_text(encoding="utf-8"))["session_id"]
        == "sess_abc123"
    )


def test_import_cookies_to_session_cache_accepts_object_format(tmp_path: Path) -> None:
    source_path = tmp_path / "session.json"
    target_path = tmp_path / "cookies.json"
    source_path.write_text(
        '{"cookies": {"clerk_active_context": "sess_xyz:", "__session": "token"}, "headers": {"x-test": "1"}}',
        encoding="utf-8",
    )

    destination, payload = import_cookies_to_session_cache(
        source_path, target_path=target_path
    )

    assert destination == target_path
    assert payload["session_id"] == "sess_xyz"
    assert payload["headers"] == {"x-test": "1"}
