from pathlib import Path

import pytest

from adapta.models import PromptRequest
from adapta.services.prompt_service import build_prompt_request, execute_prompt


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        self.calls.append((model_backend, prompt))
        return "2"


def test_build_prompt_request_from_inline_text() -> None:
    request = build_prompt_request(
        model_key="gpt",
        prompt="olá",
        prompt_file=None,
        output=None,
    )

    assert isinstance(request, PromptRequest)
    assert request.prompt_text == "olá"
    assert request.prompt_source == "inline"


def test_build_prompt_request_from_file(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("oi", encoding="utf-8")

    request = build_prompt_request(
        model_key="gpt",
        prompt=None,
        prompt_file=prompt_file,
        output=tmp_path / "saida.txt",
    )

    assert request.prompt_text == "oi"
    assert request.prompt_source == "file"
    assert request.output_path == tmp_path / "saida.txt"


def test_build_prompt_request_rejects_multiple_sources(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("oi", encoding="utf-8")

    with pytest.raises(ValueError):
        build_prompt_request("gpt", "oi", prompt_file, None)


def test_build_prompt_request_rejects_missing_sources() -> None:
    with pytest.raises(ValueError):
        build_prompt_request("gpt", None, None, None)


def test_build_prompt_request_rejects_empty_file(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("   ", encoding="utf-8")

    with pytest.raises(ValueError):
        build_prompt_request("gpt", None, prompt_file, None)


@pytest.mark.anyio
async def test_execute_prompt_calls_client() -> None:
    client = DummyClient()
    request = PromptRequest(
        model_key="gpt",
        prompt_text="quanto é 1+1 responda somente o valor",
        prompt_source="inline",
        output_path=None,
    )

    response = await execute_prompt(client, request, model_backend="GPT_5")

    assert response.text == "2"
    assert client.calls == [("GPT_5", "quanto é 1+1 responda somente o valor")]
