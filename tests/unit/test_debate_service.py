from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapta.models import DebateConfig
from adapta.services.debate_service import (
    DebateControlDecision,
    format_turn_label,
    load_debate_agents,
    persist_debate_agents,
    run_controlled_debate,
    run_debate,
)


class DummyDebateClient:
    def __init__(self) -> None:
        self.chat_calls: list[
            tuple[str, str, list[dict[str, str]], list[str] | None]
        ] = []
        self.prompt_calls: list[tuple[str, str]] = []
        self.deleted: list[str] = []
        self.uploaded: list[str] = []

    async def chat(
        self, *, model_backend: str, messages: list[dict[str, str]], chat_id: str
    ) -> str:
        self.chat_calls.append((model_backend, chat_id, list(messages), None))
        return f"resposta-{model_backend}-{len(messages)}"

    async def chat_with_files(
        self,
        *,
        model_backend: str,
        messages: list[dict[str, str]],
        chat_id: str,
        files: list[dict[str, object]],
    ) -> str:
        self.chat_calls.append(
            (
                model_backend,
                chat_id,
                list(messages),
                [str(file["filename"]) for file in files],
            )
        )
        return f"resposta-{model_backend}-{len(messages)}"

    async def upload_file(self, file_path: Path) -> dict[str, object]:
        self.uploaded.append(file_path.name)
        return {
            "filename": file_path.name,
            "url": f"https://files.example/{file_path.name}",
            "size": file_path.stat().st_size,
            "mediaType": "application/pdf",
            "path": f"uploads/{file_path.name}",
        }

    async def prompt(self, *, model_backend: str, prompt: str) -> str:
        self.prompt_calls.append((model_backend, prompt))
        return f"conclusao-{model_backend}"

    async def delete_chat(self, chat_id: str | list[str]) -> None:
        if isinstance(chat_id, list):
            self.deleted.extend(chat_id)
            return
        self.deleted.append(chat_id)


def _write_config(path: Path, payload: dict[str, dict[str, str]]) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_debate_agents_rejects_single_agent(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path / "debate.json",
        {"A1": {"model": "claude", "prompt": "arquiteto"}},
    )

    with pytest.raises(ValueError, match="ao menos 2 agentes"):
        load_debate_agents(config_path)


def test_persist_debate_agents_writes_expected_json(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path / "input.json",
        {
            "A1": {"model": "claude", "prompt": "arquiteto"},
            "A2": {"model": "gpt", "prompt": "desenvolvedor"},
        },
    )
    agents = load_debate_agents(config_path)
    destination = tmp_path / "debate.json"

    persist_debate_agents(agents, destination)

    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert saved == {
        "A1": {"model": "claude", "prompt": "arquiteto"},
        "A2": {"model": "gpt", "prompt": "desenvolvedor"},
    }


def test_load_debate_agents_resolves_optional_persona_path(tmp_path: Path) -> None:
    persona_path = tmp_path / "persona.md"
    persona_path.write_text("# Você é Cliente Cético\n", encoding="utf-8")
    config_path = _write_config(
        tmp_path / "debate.json",
        {
            "A1": {
                "model": "claude",
                "prompt": "arquiteto",
                "persona": "persona.md",
            },
            "A2": {"model": "gpt", "prompt": "desenvolvedor"},
        },
    )

    agents = load_debate_agents(config_path)

    assert agents[0].persona_path == persona_path.resolve()
    assert agents[1].persona_path is None


def test_load_debate_agents_resolves_persona_short_name_from_user_directory(
    monkeypatch, tmp_path: Path
) -> None:
    persona_dir = tmp_path / ".adapta" / "persona"
    persona_dir.mkdir(parents=True)
    persona_path = persona_dir / "cliente-cetico.md"
    persona_path.write_text("# Você é Cliente Cético\n", encoding="utf-8")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    config_path = _write_config(
        tmp_path / "debate.json",
        {
            "A1": {
                "model": "claude",
                "prompt": "arquiteto",
                "persona": "cliente-cetico",
            },
            "A2": {"model": "gpt", "prompt": "desenvolvedor"},
        },
    )

    agents = load_debate_agents(config_path)

    assert agents[0].persona_path == persona_path.resolve()


@pytest.mark.anyio
async def test_run_debate_orchestrates_rounds_and_cleanup(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path / "debate.json",
        {
            "A1": {"model": "claude", "prompt": "arquiteto"},
            "A2": {"model": "gpt", "prompt": "desenvolvedor"},
        },
    )
    agents = load_debate_agents(config_path)
    config = DebateConfig(
        agents=agents,
        rounds=2,
        topic_prompt="Defina uma arquitetura",
        conclusion_model_key="gemini",
        output_path=None,
        config_source="argument",
    )
    emitted: list[str] = []
    client = DummyDebateClient()

    result = await run_debate(
        client,
        config,
        emit_turn=lambda turn: emitted.append(format_turn_label(turn)),
    )

    assert len(result.rounds) == 2
    assert result.final_conclusion == "conclusao-GEMINI_3_PRO_PREVIEW"
    assert emitted == [
        "A1 Rodada 1",
        "A2 Rodada 1",
        "A1 Rodada 2",
        "A2 Rodada 2",
    ]
    assert len(client.chat_calls) == 4
    assert len(client.deleted) == 2


@pytest.mark.anyio
async def test_run_debate_uploads_attachments_once_and_reuses_them(
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path / "debate.json",
        {
            "A1": {"model": "claude", "prompt": "arquiteto"},
            "A2": {"model": "gpt", "prompt": "desenvolvedor"},
        },
    )
    attachment_a = tmp_path / "a.pdf"
    attachment_b = tmp_path / "b.pdf"
    attachment_a.write_bytes(b"%PDF-1.4\n")
    attachment_b.write_bytes(b"%PDF-1.4\n")
    agents = load_debate_agents(config_path)
    config = DebateConfig(
        agents=agents,
        rounds=2,
        topic_prompt="Defina uma arquitetura",
        conclusion_model_key="gemini",
        output_path=None,
        config_source="argument",
        file_paths=[attachment_a, attachment_b],
    )
    client = DummyDebateClient()

    await run_debate(client, config)

    assert client.uploaded == ["a.pdf", "b.pdf"]
    assert len(client.chat_calls) == 4
    assert all(call[3] == ["a.pdf", "b.pdf"] for call in client.chat_calls)


@pytest.mark.anyio
async def test_run_debate_incorporates_persona_file_into_agent_prompt(
    tmp_path: Path,
) -> None:
    persona_path = tmp_path / "persona.md"
    persona_path.write_text(
        "# Você é Cliente Cético\nQuestione promessas.", encoding="utf-8"
    )
    config_path = _write_config(
        tmp_path / "debate.json",
        {
            "A1": {
                "model": "claude",
                "prompt": "arquiteto",
                "persona": str(persona_path),
            },
            "A2": {"model": "gpt", "prompt": "desenvolvedor"},
        },
    )
    agents = load_debate_agents(config_path)
    config = DebateConfig(
        agents=agents,
        rounds=1,
        topic_prompt="Avalie uma proposta",
        conclusion_model_key="gemini",
        output_path=None,
        config_source="argument",
    )
    client = DummyDebateClient()

    await run_debate(client, config)

    first_prompt = client.chat_calls[0][2][0]["content"]
    assert "# Você é Cliente Cético" in first_prompt
    assert "Questione promessas." in first_prompt


@pytest.mark.anyio
async def test_run_controlled_debate_allows_manual_reply_and_early_conclusion(
    tmp_path: Path,
) -> None:
    config_path = _write_config(
        tmp_path / "debate.json",
        {
            "A1": {"model": "claude", "prompt": "arquiteto"},
            "A2": {"model": "gpt", "prompt": "desenvolvedor"},
        },
    )
    agents = load_debate_agents(config_path)
    config = DebateConfig(
        agents=agents,
        rounds=2,
        topic_prompt="Avalie uma proposta",
        conclusion_model_key="gemini",
        output_path=None,
        config_source="argument",
    )
    decisions = iter(
        [
            DebateControlDecision(
                action="respond_one",
                target_agent_id="A2",
                user_message="Responda ao meu contra-argumento.",
            ),
            DebateControlDecision(action="conclude"),
        ]
    )
    client = DummyDebateClient()

    result = await run_controlled_debate(
        client,
        config,
        control_callback=lambda turn, agents: next(decisions),
    )

    assert result.final_conclusion == "conclusao-GEMINI_3_PRO_PREVIEW"
    assert len(result.rounds) == 1
    assert len(result.rounds[0].turns) == 2
    assert len(client.chat_calls) == 2
    assert "Responda ao meu contra-argumento." in client.chat_calls[1][2][-1]["content"]


def test_format_turn_label_uses_agent_and_round() -> None:
    config = DebateConfig(
        agents=[],
        rounds=1,
        topic_prompt="tema",
        conclusion_model_key="gemini",
        output_path=None,
        config_source="test",
    )
    del config

    from adapta.models import DebateTurn

    turn = DebateTurn(
        round_number=1,
        agent_id="Agente 1",
        model_key="claude",
        prompt_sent="prompt",
        response_text="resposta",
        status="success",
    )

    assert format_turn_label(turn) == "Agente 1 Rodada 1"
