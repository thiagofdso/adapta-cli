from __future__ import annotations

import json
import os
from collections import OrderedDict
from pathlib import Path
from typing import Callable

from adapta.models import (
    DebateAgentConfig,
    DebateConfig,
    DebateResult,
    DebateRound,
    DebateTurn,
)
from adapta.registry import get_model_option
from adapta.services.persona_service import get_persona_directory
from adapta.services.chat_service import (
    close_chat_sessions,
    create_chat_session,
    send_chat_message,
)
from adapta.services.output_service import format_debate_result, persist_output
from adapta.services.prompt_service import normalize_file_paths


TurnEmitter = Callable[[DebateTurn], None]


def _resolve_persona_path(persona_value: str, config_path: Path) -> Path:
    candidate_path = Path(persona_value)
    if candidate_path.is_absolute():
        return candidate_path.resolve()

    # Nome curto como `cliente-cetico` ou `cliente-cetico.md`
    if candidate_path.parent == Path(".") and not candidate_path.suffix:
        persona_name = f"{candidate_path.name}.md"
        return (get_persona_directory() / persona_name).resolve()

    return (config_path.parent / candidate_path).resolve()


def load_debate_agents(config_path: Path) -> list[DebateAgentConfig]:
    try:
        raw_content = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"Não foi possível ler o arquivo de configuração: {config_path}"
        ) from exc

    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError("Arquivo de configuração inválido: JSON malformado.") from exc

    if not isinstance(payload, dict):
        raise ValueError("Arquivo de configuração inválido: esperado um objeto JSON.")

    agents: list[DebateAgentConfig] = []
    for agent_id, raw_agent in payload.items():
        if not isinstance(raw_agent, dict):
            raise ValueError(f"Configuração inválida para o agente {agent_id}.")

        normalized_id = str(agent_id).strip()
        model_key = get_model_option(str(raw_agent.get("model", "")).strip()).key
        prompt = str(raw_agent.get("prompt", "")).strip()
        persona_value = str(raw_agent.get("persona", "")).strip()
        persona_path = None
        if persona_value:
            persona_path = _resolve_persona_path(persona_value, config_path)
            if not persona_path.exists() or not persona_path.is_file():
                raise ValueError(
                    f"Arquivo de persona não encontrado para o agente {normalized_id}: {persona_path}"
                )

        if not normalized_id:
            raise ValueError("Todo agente precisa de um identificador.")
        if not prompt:
            raise ValueError(f"O prompt do agente {normalized_id} não pode ser vazio.")

        agents.append(
            DebateAgentConfig(
                agent_id=normalized_id,
                model_key=model_key,
                prompt=prompt,
                persona_path=persona_path,
            )
        )

    if len(agents) < 2:
        raise ValueError("O debate exige ao menos 2 agentes.")
    return agents


def persist_debate_agents(agents: list[DebateAgentConfig], destination: Path) -> None:
    payload: OrderedDict[str, dict[str, str]] = OrderedDict()
    for agent in agents:
        payload[agent.agent_id] = {
            "model": agent.model_key,
            "prompt": agent.prompt,
        }
        if agent.persona_path is not None:
            payload[agent.agent_id]["persona"] = str(agent.persona_path)
    destination.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def _load_persona_content(agent: DebateAgentConfig) -> str:
    if agent.persona_path is None:
        return ""
    try:
        return agent.persona_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ValueError(
            f"Não foi possível ler o arquivo de persona do agente {agent.agent_id}: {agent.persona_path}"
        ) from exc


def resolve_debate_config_path(explicit: Path | None) -> tuple[Path | None, str]:
    if explicit is not None:
        return explicit, "argument"

    env_path = os.environ.get("ADAPTA_DEBATE_CONFIG")
    if env_path:
        return Path(env_path), "environment"

    return None, "interactive"


def build_debate_config(
    *,
    agents: list[DebateAgentConfig],
    rounds: int,
    topic_prompt: str,
    conclusion_model_key: str | None,
    output_path: Path | None,
    config_source: str,
    file_paths: list[Path] | None = None,
) -> DebateConfig:
    normalized_prompt = topic_prompt.strip()
    if not normalized_prompt:
        raise ValueError("Informe o prompt principal do debate via --prompt.")
    if len(agents) < 2:
        raise ValueError("O debate exige ao menos 2 agentes.")
    if rounds < 1:
        raise ValueError("Informe um número de rodadas maior que zero.")

    normalized_conclusion_model = get_model_option(conclusion_model_key or "gemini").key
    return DebateConfig(
        agents=agents,
        rounds=rounds,
        topic_prompt=normalized_prompt,
        conclusion_model_key=normalized_conclusion_model,
        output_path=output_path,
        config_source=config_source,
        file_paths=normalize_file_paths(file_paths),
    )


def format_turn_label(turn: DebateTurn) -> str:
    return f"{turn.agent_id} Rodada {turn.round_number}"


def build_final_conclusion_prompt(result: DebateResult) -> str:
    parts = [
        "Você é o agente responsável pela conclusão final de um debate multiagente.",
        f'Tema do debate: "{result.config.topic_prompt}".',
        "Sintetize as contribuições finais dos agentes em português, com uma resposta única e objetiva.",
        "",
    ]
    for debate_round in result.rounds:
        parts.append(f"# Rodada {debate_round.round_number}")
        for turn in debate_round.turns:
            parts.append(f"## {turn.agent_id}")
            parts.append(turn.response_text)
            parts.append("")
    return "\n".join(parts).strip()


def _build_turn_prompt(
    *,
    config: DebateConfig,
    agent: DebateAgentConfig,
    round_number: int,
    previous_responses: dict[str, str],
) -> str:
    base_lines = [
        f"Você é {agent.agent_id}. Responda sempre em português.",
        f"Instruções específicas: {agent.prompt}",
        f'Tema do debate: "{config.topic_prompt}".',
        f"Rodada {round_number} de {config.rounds}.",
    ]

    persona_content = _load_persona_content(agent)
    if persona_content:
        base_lines.extend(
            [
                "Assuma também a seguinte persona durante todo o debate:",
                persona_content,
            ]
        )

    if round_number == 1:
        base_lines.append(
            "Apresente sua posição inicial detalhada e não faça perguntas ao usuário."
        )
        return "\n".join(base_lines)

    other_responses = [
        f"{other_agent}: {response}"
        for other_agent, response in previous_responses.items()
        if other_agent != agent.agent_id
    ]
    if other_responses:
        base_lines.append(
            "Considere as respostas da rodada anterior dos outros agentes:"
        )
        base_lines.extend(other_responses)

    if round_number == config.rounds:
        base_lines.append("Forneça sua resposta final e conclusiva para o debate.")
    else:
        base_lines.append("Refine sua posição considerando os demais agentes.")

    return "\n".join(base_lines)


async def run_debate(
    client,
    config: DebateConfig,
    emit_turn: TurnEmitter | None = None,
) -> DebateResult:
    sessions = {
        agent.agent_id: create_chat_session(model_key=agent.model_key)
        for agent in config.agents
    }
    debate_rounds: list[DebateRound] = []
    cleanup_warnings: list[str] = []
    previous_responses: dict[str, str] = {}
    uploaded_files = [await client.upload_file(path) for path in config.file_paths]

    try:
        for round_number in range(1, config.rounds + 1):
            turns: list[DebateTurn] = []
            current_responses: dict[str, str] = {}
            for agent in config.agents:
                prompt_text = _build_turn_prompt(
                    config=config,
                    agent=agent,
                    round_number=round_number,
                    previous_responses=previous_responses,
                )
                session = sessions[agent.agent_id]
                model_backend = get_model_option(agent.model_key).backend_name
                try:
                    response_text = await send_chat_message(
                        client,
                        session,
                        model_backend=model_backend,
                        prompt_text=prompt_text,
                        uploaded_files=uploaded_files,
                    )
                    status = "success" if response_text.strip() else "empty"
                    if not response_text.strip():
                        response_text = f"{agent.agent_id} retornou resposta vazia."
                except Exception as exc:  # noqa: BLE001
                    status = "error"
                    response_text = f"Erro para {agent.agent_id}: {exc}"

                turn = DebateTurn(
                    round_number=round_number,
                    agent_id=agent.agent_id,
                    model_key=agent.model_key,
                    prompt_sent=prompt_text,
                    response_text=response_text,
                    status=status,
                )
                turns.append(turn)
                current_responses[agent.agent_id] = response_text

                if emit_turn is not None:
                    emit_turn(turn)

            debate_rounds.append(DebateRound(round_number=round_number, turns=turns))
            previous_responses = current_responses

        provisional_result = DebateResult(
            config=config,
            rounds=debate_rounds,
            final_conclusion="",
            saved_path=None,
        )
        final_conclusion = await client.prompt(
            model_backend=get_model_option(config.conclusion_model_key).backend_name,
            prompt=build_final_conclusion_prompt(provisional_result),
        )
        result = DebateResult(
            config=config,
            rounds=debate_rounds,
            final_conclusion=final_conclusion,
            saved_path=config.output_path,
            cleanup_warnings=cleanup_warnings,
        )
        if config.output_path is not None:
            persist_output(format_debate_result(result), config.output_path)
        return result
    finally:
        try:
            await close_chat_sessions(client, list(sessions.values()))
        except Exception as exc:  # noqa: BLE001
            cleanup_warnings.append(f"Falha ao limpar chats remotos: {exc}")
