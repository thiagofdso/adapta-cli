from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from adapta.client import (
    AGENT_BASE_URL,
    API_AGENT_BASE_URL,
    AdaptaConversationClient,
    AdaptaHttpSession,
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
