from __future__ import annotations

import asyncio
import json
import os
from collections import OrderedDict
from dataclasses import dataclass
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


@dataclass(frozen=True)
class DebateControlDecision:
    action: str
    target_agent_id: str | None = None
    source_agent_id: str | None = None
    user_message: str | None = None


def _resolve_persona_path(persona_value: str, config_path: Path, data_dir: Path) -> Path:
    candidate_path = Path(persona_value)
    if candidate_path.is_absolute():
        return candidate_path.resolve()

    # Nome curto como `cliente-cetico` ou `cliente-cetico.md`
    if candidate_path.parent == Path(".") and not candidate_path.suffix:
        persona_name = f"{candidate_path.name}.md"
        return (get_persona_directory(data_dir) / persona_name).resolve()

    return (config_path.parent / candidate_path).resolve()


def load_debate_agents(config_path: Path, data_dir: Path) -> list[DebateAgentConfig]:
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
            persona_path = _resolve_persona_path(persona_value, config_path, data_dir)
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
        raise ValueError(
            "Informe o prompt principal do debate via --prompt ou --prompt-file."
        )
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


def _build_control_prompt(
    *,
    config: DebateConfig,
    agent: DebateAgentConfig,
    instruction: str,
    context_lines: list[str],
) -> str:
    base_lines = [
        f"Você é {agent.agent_id}. Responda sempre em português.",
        f"Instruções específicas: {agent.prompt}",
        f'Tema do debate: "{config.topic_prompt}".',
        "Você está em uma intervenção controlada do usuário dentro do debate.",
        instruction,
    ]
    persona_content = _load_persona_content(agent)
    if persona_content:
        base_lines.extend(
            [
                "Assuma também a seguinte persona durante todo o debate:",
                persona_content,
            ]
        )
    base_lines.extend(context_lines)
    return "\n".join(base_lines)


async def _send_turn(
    *,
    client,
    config: DebateConfig,
    session,
    agent: DebateAgentConfig,
    round_number: int,
    prompt_text: str,
    uploaded_files: list[dict[str, object]],
) -> DebateTurn:
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

    return DebateTurn(
        round_number=round_number,
        agent_id=agent.agent_id,
        model_key=agent.model_key,
        prompt_sent=prompt_text,
        response_text=response_text,
        status=status,
    )


async def _finalize_debate_result(
    *,
    client,
    config: DebateConfig,
    debate_rounds: list[DebateRound],
    cleanup_warnings: list[str],
) -> DebateResult:
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
            turns = await asyncio.gather(
                *[
                    _send_turn(
                        client=client,
                        config=config,
                        session=sessions[agent.agent_id],
                        agent=agent,
                        round_number=round_number,
                        prompt_text=_build_turn_prompt(
                            config=config,
                            agent=agent,
                            round_number=round_number,
                            previous_responses=previous_responses,
                        ),
                        uploaded_files=uploaded_files,
                    )
                    for agent in config.agents
                ]
            )
            current_responses: dict[str, str] = {}
            for turn in turns:
                current_responses[turn.agent_id] = turn.response_text

                if emit_turn is not None:
                    emit_turn(turn)

            debate_rounds.append(DebateRound(round_number=round_number, turns=turns))
            previous_responses = current_responses

        return await _finalize_debate_result(
            client=client,
            config=config,
            debate_rounds=debate_rounds,
            cleanup_warnings=cleanup_warnings,
        )
    finally:
        try:
            await close_chat_sessions(client, list(sessions.values()))
        except Exception as exc:  # noqa: BLE001
            cleanup_warnings.append(f"Falha ao limpar chats remotos: {exc}")


async def run_controlled_debate(
    client,
    config: DebateConfig,
    control_callback: Callable[
        [DebateTurn, list[DebateAgentConfig]], DebateControlDecision
    ],
    emit_turn: TurnEmitter | None = None,
) -> DebateResult:
    sessions = {
        agent.agent_id: create_chat_session(model_key=agent.model_key)
        for agent in config.agents
    }
    agent_map = {agent.agent_id: agent for agent in config.agents}
    debate_rounds: list[DebateRound] = []
    cleanup_warnings: list[str] = []
    previous_responses: dict[str, str] = {}
    latest_responses: dict[str, str] = {}
    uploaded_files = [await client.upload_file(path) for path in config.file_paths]

    async def _emit_and_track(
        turn: DebateTurn,
        turns: list[DebateTurn],
        current_responses: dict[str, str],
    ) -> None:
        turns.append(turn)
        current_responses[turn.agent_id] = turn.response_text
        latest_responses[turn.agent_id] = turn.response_text
        if emit_turn is not None:
            emit_turn(turn)

    async def _handle_control(
        last_turn: DebateTurn,
        round_number: int,
        turns: list[DebateTurn],
        current_responses: dict[str, str],
    ) -> bool:
        while True:
            decision = control_callback(last_turn, config.agents)
            if decision.action == "continue":
                return False
            if decision.action == "conclude":
                return True
            if decision.action == "respond_one":
                target_id = decision.target_agent_id or ""
                target_agent = agent_map.get(target_id)
                if target_agent is None:
                    raise ValueError(f"Agente inválido para intervenção: {target_id}")
                prompt_text = _build_control_prompt(
                    config=config,
                    agent=target_agent,
                    instruction="Responda diretamente à intervenção do usuário abaixo.",
                    context_lines=[decision.user_message or ""],
                )
                turn = await _send_turn(
                    client=client,
                    config=config,
                    session=sessions[target_id],
                    agent=target_agent,
                    round_number=round_number,
                    prompt_text=prompt_text,
                    uploaded_files=uploaded_files,
                )
                await _emit_and_track(turn, turns, current_responses)
                if await _handle_control(turn, round_number, turns, current_responses):
                    return True
                return False
            if decision.action == "respond_all":
                for target_agent in config.agents:
                    prompt_text = _build_control_prompt(
                        config=config,
                        agent=target_agent,
                        instruction="Responda diretamente à intervenção comum do usuário abaixo.",
                        context_lines=[decision.user_message or ""],
                    )
                    turn = await _send_turn(
                        client=client,
                        config=config,
                        session=sessions[target_agent.agent_id],
                        agent=target_agent,
                        round_number=round_number,
                        prompt_text=prompt_text,
                        uploaded_files=uploaded_files,
                    )
                    await _emit_and_track(turn, turns, current_responses)
                    if await _handle_control(
                        turn, round_number, turns, current_responses
                    ):
                        return True
                return False
            if decision.action == "agent_to_agent":
                target_id = decision.target_agent_id or ""
                source_id = decision.source_agent_id or ""
                target_agent = agent_map.get(target_id)
                if target_agent is None:
                    raise ValueError(f"Agente inválido para intervenção: {target_id}")
                source_text = latest_responses.get(source_id)
                if source_text is None:
                    raise ValueError(
                        f"Ainda não há resposta registrada para {source_id}."
                    )
                prompt_text = _build_control_prompt(
                    config=config,
                    agent=target_agent,
                    instruction=f"Responda especificamente à última resposta de {source_id}.",
                    context_lines=[f"{source_id}: {source_text}"],
                )
                turn = await _send_turn(
                    client=client,
                    config=config,
                    session=sessions[target_id],
                    agent=target_agent,
                    round_number=round_number,
                    prompt_text=prompt_text,
                    uploaded_files=uploaded_files,
                )
                await _emit_and_track(turn, turns, current_responses)
                if await _handle_control(turn, round_number, turns, current_responses):
                    return True
                return False
            if decision.action == "agent_to_all":
                target_id = decision.target_agent_id or ""
                target_agent = agent_map.get(target_id)
                if target_agent is None:
                    raise ValueError(f"Agente inválido para intervenção: {target_id}")
                context_lines = [
                    f"{agent_id}: {response_text}"
                    for agent_id, response_text in latest_responses.items()
                    if agent_id != target_id
                ]
                if not context_lines:
                    raise ValueError(
                        "Ainda não há respostas de outros agentes para esse passo."
                    )
                prompt_text = _build_control_prompt(
                    config=config,
                    agent=target_agent,
                    instruction="Responda considerando as últimas respostas de todos os outros agentes abaixo.",
                    context_lines=context_lines,
                )
                turn = await _send_turn(
                    client=client,
                    config=config,
                    session=sessions[target_id],
                    agent=target_agent,
                    round_number=round_number,
                    prompt_text=prompt_text,
                    uploaded_files=uploaded_files,
                )
                await _emit_and_track(turn, turns, current_responses)
                if await _handle_control(turn, round_number, turns, current_responses):
                    return True
                return False
            raise ValueError(f"Ação de controle inválida: {decision.action}")

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
                turn = await _send_turn(
                    client=client,
                    config=config,
                    session=sessions[agent.agent_id],
                    agent=agent,
                    round_number=round_number,
                    prompt_text=prompt_text,
                    uploaded_files=uploaded_files,
                )
                await _emit_and_track(turn, turns, current_responses)
                if await _handle_control(turn, round_number, turns, current_responses):
                    debate_rounds.append(
                        DebateRound(round_number=round_number, turns=turns)
                    )
                    return await _finalize_debate_result(
                        client=client,
                        config=config,
                        debate_rounds=debate_rounds,
                        cleanup_warnings=cleanup_warnings,
                    )

            debate_rounds.append(DebateRound(round_number=round_number, turns=turns))
            previous_responses = dict(current_responses)

        return await _finalize_debate_result(
            client=client,
            config=config,
            debate_rounds=debate_rounds,
            cleanup_warnings=cleanup_warnings,
        )
    finally:
        try:
            await close_chat_sessions(client, list(sessions.values()))
        except Exception as exc:  # noqa: BLE001
            cleanup_warnings.append(f"Falha ao limpar chats remotos: {exc}")
