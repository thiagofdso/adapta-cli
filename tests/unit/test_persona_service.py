from __future__ import annotations

from pathlib import Path

import pytest

from adapta.services import persona_service


def test_build_persona_questionnaire_accepts_required_fields_only() -> None:
    questionnaire = persona_service.build_persona_questionnaire(
        nome="Ana Lider",
        cargo="Gerente de Produto",
    )

    assert questionnaire.nome == "Ana Lider"
    assert questionnaire.cargo == "Gerente de Produto"
    assert questionnaire.setor == ""
    assert questionnaire.motiva_desmotiva == ""


def test_build_persona_questionnaire_rejects_empty_cargo() -> None:
    with pytest.raises(ValueError, match="cargo"):
        persona_service.build_persona_questionnaire(nome="Ana", cargo="   ")


def test_normalize_persona_name_returns_safe_slug() -> None:
    display_name, slug = persona_service.normalize_persona_name(
        "  Ana Líder / Produto  "
    )

    assert display_name == "Ana Líder / Produto"
    assert slug == "ana-lider-produto"


def test_resolve_persona_output_path_uses_home_directory_cross_platform(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(persona_service.Path, "home", lambda: tmp_path)

    output_path = persona_service.resolve_persona_output_path("Ana Lider")

    assert output_path == (tmp_path / ".adapta" / "persona" / "ana-lider.md").resolve()


def test_build_persona_prompt_preserves_empty_fields() -> None:
    questionnaire = persona_service.build_persona_questionnaire(
        nome="Ana",
        cargo="Gerente",
    )

    prompt = persona_service.build_persona_prompt(questionnaire)

    assert '"nome": "Ana"' in prompt
    assert '"cargo": "Gerente"' in prompt
    assert '"setor": ""' in prompt
    assert "VOCÊ É UM GERADOR INTELIGENTE DE PROMPTS DE PERSONA" in prompt
    assert persona_service.PERSONA_CONTENT_START in prompt
    assert persona_service.PERSONA_CONTENT_END in prompt


def test_extract_persona_content_prefers_delimited_block() -> None:
    raw = "Introdução da LLM\n<<<PERSONA_CONTENT_START>>>\n# Você é Ana\n\nConteúdo\n<<<PERSONA_CONTENT_END>>>\nObservação final"

    extracted = persona_service.extract_persona_content(raw)

    assert extracted == "# Você é Ana\n\nConteúdo\n"


def test_extract_persona_content_falls_back_to_heading_for_old_files() -> None:
    raw = "Vou montar a persona agora.\n\n# Você é Ana\n\nConteúdo\n"

    extracted = persona_service.extract_persona_content(raw)

    assert extracted == "# Você é Ana\n\nConteúdo\n"


def test_save_persona_document_rejects_existing_file_without_confirmation(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "ana.md"
    output_path.write_text("anterior", encoding="utf-8")

    with pytest.raises(FileExistsError):
        persona_service.save_persona_document(
            text="# Nova persona\n",
            output_path=output_path,
            overwrite=False,
        )


def test_save_persona_answers_writes_json_file(tmp_path: Path) -> None:
    questionnaire = persona_service.build_persona_questionnaire(
        nome="Ana Lider",
        cargo="Gerente de Produto",
        setor="SaaS",
    )
    json_path = tmp_path / "ana-lider.json"

    saved_path = persona_service.save_persona_answers(
        questionnaire,
        json_path,
        overwrite=True,
    )

    assert saved_path == json_path
    assert '"nome": "Ana Lider"' in json_path.read_text(encoding="utf-8")


def test_load_persona_questionnaire_from_json_file(tmp_path: Path) -> None:
    json_path = tmp_path / "ana-lider.json"
    json_path.write_text(
        '{"nome":"Ana Lider","cargo":"Gerente de Produto","setor":"SaaS"}',
        encoding="utf-8",
    )

    questionnaire = persona_service.load_persona_questionnaire_from_file(json_path)

    assert questionnaire.nome == "Ana Lider"
    assert questionnaire.cargo == "Gerente de Produto"
    assert questionnaire.setor == "SaaS"


@pytest.mark.anyio
async def test_generate_persona_document_cleans_up_chat_on_success() -> None:
    questionnaire = persona_service.build_persona_questionnaire(
        nome="Ana",
        cargo="Gerente",
    )

    class DummyClient:
        def __init__(self) -> None:
            self.chat_calls: list[tuple[str, str, list[dict[str, str]]]] = []
            self.deleted_chats: list[str] = []

        async def chat(
            self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
        ) -> str:
            self.chat_calls.append((model_backend, chat_id, list(messages)))
            return "<<<PERSONA_CONTENT_START>>>\n# Persona\n<<<PERSONA_CONTENT_END>>>"

        async def delete_chat(self, chat_id: str) -> None:
            self.deleted_chats.append(chat_id)

    client = DummyClient()

    result = await persona_service.generate_persona_document(
        client, questionnaire, model_key="claude"
    )

    assert result.text == "# Persona\n"
    assert result.cleanup_warning is None
    assert client.chat_calls[0][0] == "CLAUDE_4_5_SONNET"
    assert client.deleted_chats == [client.chat_calls[0][1]]


@pytest.mark.anyio
async def test_generate_persona_document_reports_cleanup_warning_without_failing() -> (
    None
):
    questionnaire = persona_service.build_persona_questionnaire(
        nome="Ana",
        cargo="Gerente",
    )

    class DummyClient:
        async def chat(
            self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
        ) -> str:
            return "<<<PERSONA_CONTENT_START>>>\n# Persona\n<<<PERSONA_CONTENT_END>>>"

        async def delete_chat(self, chat_id: str) -> None:
            raise RuntimeError("cleanup falhou")

    result = await persona_service.generate_persona_document(
        DummyClient(), questionnaire, model_key="claude"
    )

    assert result.text == "# Persona\n"
    assert result.cleanup_warning == "Falha ao limpar chat remoto: cleanup falhou"


@pytest.mark.anyio
async def test_generate_persona_document_accepts_custom_model_key() -> None:
    questionnaire = persona_service.build_persona_questionnaire(
        nome="Ana",
        cargo="Gerente",
    )

    class DummyClient:
        def __init__(self) -> None:
            self.model_backend: str | None = None

        async def chat(
            self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
        ) -> str:
            self.model_backend = model_backend
            return "<<<PERSONA_CONTENT_START>>>\n# Persona\n<<<PERSONA_CONTENT_END>>>"

        async def delete_chat(self, chat_id: str) -> None:
            return None

    client = DummyClient()

    await persona_service.generate_persona_document(
        client, questionnaire, model_key="gpt"
    )

    assert client.model_backend == "GPT_5"
