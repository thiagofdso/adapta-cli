from __future__ import annotations
import json
from dataclasses import replace
from pathlib import Path

import typer

from adapta.client import create_client, import_cookies_to_session_cache
from adapta.config import load_settings
from adapta.models import DebateAgentConfig
from adapta.registry import get_model_option, list_model_options, resolve_model_key
from adapta.runtime import run_async
from adapta.services.chat_service import (
    close_chat_session,
    create_chat_session,
    send_chat_message,
)
from adapta.services.debate_service import (
    DebateControlDecision,
    build_debate_config,
    format_turn_label,
    load_debate_agents,
    persist_debate_agents,
    resolve_debate_config_path,
    run_controlled_debate,
    run_debate,
)
from adapta.services.destilador_service import (
    build_distillation_request,
    distill_documents,
)
from adapta.services.pipeline_service import build_pipeline_request, run_pipeline
from adapta.services.output_service import persist_output
from adapta.services.persona_service import (
    PERSONA_BLOCKS,
    build_persona_questionnaire,
    generate_persona_document,
    get_persona_directory,
    load_persona_questionnaire_from_file,
    questionnaire_to_dict,
    resolve_persona_answers_path,
    resolve_persona_output_path,
    save_persona_answers,
    save_persona_document,
)
from adapta.services.prompt_service import (
    build_prompt_request,
    execute_prompt,
    normalize_file_paths,
)


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


def _fail(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def _select_model_interactively(prompt_label: str = "Modelo") -> str:
    options = list_model_options()
    typer.echo("Selecione um modelo:")
    for index, option in enumerate(options, start=1):
        typer.echo(f"{index}. {option.display_name} ({option.key})")

    raw_choice = typer.prompt(prompt_label)
    try:
        selected = options[int(raw_choice) - 1]
        return selected.key
    except (ValueError, IndexError):
        return get_model_option(raw_choice).key


def _resolve_model(explicit: str | None, default: str | None) -> str:
    if explicit or default:
        return resolve_model_key(explicit, default)
    return _select_model_interactively()


def _prompt_int(label: str, *, minimum: int) -> int:
    while True:
        raw_value = typer.prompt(label).strip()
        if not raw_value.isdigit():
            typer.echo("Informe um número inteiro válido.")
            continue
        value = int(raw_value)
        if value < minimum:
            typer.echo(f"Informe um número maior ou igual a {minimum}.")
            continue
        return value


def _prompt_required_text(label: str, empty_message: str) -> str:
    while True:
        value = typer.prompt(label).strip()
        if value:
            return value
        typer.echo(empty_message)


def _confirm_overwrite(path: Path) -> bool:
    while True:
        value = (
            typer.prompt(f"A persona já existe em {path}. Deseja sobrescrever? [s/n]")
            .strip()
            .lower()
        )
        if value in {"s", "sim", "y", "yes"}:
            return True
        if value in {"n", "nao", "não", "no"}:
            return False
        typer.echo("Responda com 's' ou 'n'.")


def _prompt_persona_name() -> tuple[str, Path, bool]:
    while True:
        raw_name = typer.prompt("Qual é o nome da persona?")
        try:
            output_path = resolve_persona_output_path(raw_name)
        except ValueError as exc:
            typer.echo(str(exc))
            continue
        if output_path.exists():
            overwrite = _confirm_overwrite(output_path)
            return raw_name.strip(), output_path, overwrite
        return raw_name.strip(), output_path, True


def _prompt_text_with_default(
    label: str,
    default: str,
    *,
    allow_empty: bool = True,
    empty_message: str | None = None,
) -> str:
    while True:
        value = typer.prompt(label, default=default, show_default=bool(default)).strip()
        if value or allow_empty:
            return value
        if empty_message is not None:
            typer.echo(empty_message)


def _collect_persona_answers(
    existing: dict[str, str] | None = None,
) -> tuple[dict[str, str], Path, bool]:
    defaults = existing or {}
    while True:
        if defaults.get("nome"):
            raw_name = _prompt_text_with_default(
                "Qual é o nome da persona?",
                defaults["nome"],
                allow_empty=False,
                empty_message="Nome da persona inválido: informe um valor não vazio.",
            )
        else:
            raw_name, output_path, overwrite = _prompt_persona_name()
            defaults = {**defaults, "nome": raw_name}
            if output_path.exists() and not overwrite:
                return {"nome": raw_name}, output_path, overwrite
            break
        try:
            output_path = resolve_persona_output_path(raw_name)
            overwrite = True
            if output_path.exists():
                overwrite = _confirm_overwrite(output_path)
            defaults["nome"] = raw_name.strip()
            break
        except ValueError as exc:
            typer.echo(str(exc))

    answers: dict[str, str] = {"nome": defaults["nome"]}
    for block_index, (block_title, questions) in enumerate(PERSONA_BLOCKS):
        typer.echo(block_title if block_index == 0 else f"\n{block_title}")
        for field, question in questions:
            if field == "nome":
                continue
            default_value = defaults.get(field, "")
            if field == "cargo":
                answers[field] = _prompt_text_with_default(
                    question,
                    default_value,
                    allow_empty=False,
                    empty_message="O cargo/título profissional não pode ser vazio.",
                )
            else:
                answers[field] = _prompt_text_with_default(
                    question,
                    default_value,
                    allow_empty=True,
                )
    return answers, output_path, overwrite


def _resolve_persona_source(
    *, input_file: Path | None, update: bool
) -> tuple[dict[str, str], Path, Path, bool]:
    if input_file is not None and update:
        raise ValueError("Use apenas uma das opções: --input-file ou --update.")

    if input_file is not None:
        questionnaire = load_persona_questionnaire_from_file(input_file)
        output_path = resolve_persona_output_path(questionnaire.nome)
        answers_path = resolve_persona_answers_path(questionnaire.nome)
        overwrite = True
        if output_path.exists() or answers_path.exists():
            overwrite = _confirm_overwrite(output_path)
        return (
            questionnaire_to_dict(questionnaire),
            output_path,
            answers_path,
            overwrite,
        )

    if update:
        update_name = _prompt_required_text(
            "Qual persona deseja atualizar?",
            "Informe o nome da persona que deseja atualizar.",
        )
        answers_path = resolve_persona_answers_path(update_name)
        questionnaire = load_persona_questionnaire_from_file(answers_path)
        answers, output_path, overwrite = _collect_persona_answers(
            questionnaire_to_dict(questionnaire)
        )
        return (
            answers,
            output_path,
            resolve_persona_answers_path(answers["nome"]),
            overwrite,
        )

    answers, output_path, overwrite = _collect_persona_answers()
    return (
        answers,
        output_path,
        resolve_persona_answers_path(answers["nome"]),
        overwrite,
    )


def _parse_file_option(value: str | None) -> list[Path]:
    if value is None:
        return []
    parts = [Path(item.strip()) for item in value.split(",") if item.strip()]
    return normalize_file_paths(parts)


def _resolve_debate_topic_prompt(
    prompt: str | None,
    prompt_file: Path | None,
) -> str:
    if prompt is not None and prompt_file is not None:
        raise ValueError("Use apenas uma das opções: --prompt ou --prompt-file.")

    if prompt_file is not None:
        try:
            content = prompt_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise ValueError(
                f"Não foi possível ler o arquivo de prompt: {prompt_file}"
            ) from exc
        if not content:
            raise ValueError("Arquivo de prompt vazio.")
        return content

    normalized_prompt = (prompt or "").strip()
    if not normalized_prompt:
        raise ValueError(
            "Informe o prompt principal do debate via --prompt ou --prompt-file."
        )
    return normalized_prompt


def _load_persona_prompt_text(identifier: str) -> str:
    persona_path = resolve_persona_output_path(identifier)
    if not persona_path.exists():
        raise ValueError(
            f"Persona não encontrada: {persona_path}. Use 'adapta persona --list' para listar."
        )
    content = persona_path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Persona vazia: {persona_path}")
    return content


def _list_personas() -> None:
    directory = get_persona_directory()
    if not directory.exists():
        typer.echo(f"Nenhuma persona encontrada em {directory}")
        return
    entries = sorted(directory.glob("*.json"))
    if not entries:
        typer.echo(f"Nenhuma persona encontrada em {directory}")
        return
    typer.echo("slug\tNome\tCargo")
    for json_file in entries:
        slug = json_file.stem
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            typer.echo(f"{slug}\t(Não foi possível ler)\t")
            continue
        nome = str(payload.get("nome") or slug)
        cargo = str(payload.get("cargo") or "")
        typer.echo(f"{slug}\t{nome}\t{cargo}")


def _select_agent_id(agents: list[DebateAgentConfig], label: str) -> str:
    typer.echo(label)
    for index, agent in enumerate(agents, start=1):
        typer.echo(f"{index}. {agent.agent_id}")
    raw_choice = typer.prompt("Seleção").strip()
    try:
        selected = agents[int(raw_choice) - 1]
        return selected.agent_id
    except (ValueError, IndexError):
        for agent in agents:
            if agent.agent_id == raw_choice:
                return agent.agent_id
    raise ValueError(f"Agente inválido: {raw_choice}")


def _prompt_control_decision(
    turn,
    agents: list[DebateAgentConfig],
) -> DebateControlDecision:
    typer.echo("1. Continuar fluxo atual")
    typer.echo("2. Responder um agente")
    typer.echo("3. Responder todos os agentes")
    typer.echo("4. Fazer um agente responder a outro")
    typer.echo("5. Fazer um agente responder a todos")
    typer.echo("6. Concluir debate")
    choice = typer.prompt("Ação após a resposta").strip()

    if choice == "1":
        return DebateControlDecision(action="continue")
    if choice == "2":
        target_agent_id = _select_agent_id(agents, "Qual agente deve responder?")
        user_message = typer.prompt("Sua resposta para esse agente").strip()
        return DebateControlDecision(
            action="respond_one",
            target_agent_id=target_agent_id,
            user_message=user_message,
        )
    if choice == "3":
        user_message = typer.prompt("Sua resposta para todos os agentes").strip()
        return DebateControlDecision(action="respond_all", user_message=user_message)
    if choice == "4":
        target_agent_id = _select_agent_id(agents, "Qual agente vai responder?")
        source_agent_id = _select_agent_id(agents, "A qual agente ele deve responder?")
        return DebateControlDecision(
            action="agent_to_agent",
            target_agent_id=target_agent_id,
            source_agent_id=source_agent_id,
        )
    if choice == "5":
        target_agent_id = _select_agent_id(
            agents, "Qual agente deve responder a todos?"
        )
        return DebateControlDecision(
            action="agent_to_all",
            target_agent_id=target_agent_id,
        )
    if choice == "6":
        return DebateControlDecision(action="conclude")
    raise ValueError(f"Ação inválida: {choice}")


@app.command()
def models() -> None:
    for option in list_model_options():
        typer.echo(
            "\t".join(
                filter(
                    None,
                    [
                        option.key,
                        option.display_name,
                        option.backend_name,
                        option.summary,
                    ],
                )
            )
        )


@app.command("list-files")
def list_files() -> None:
    try:
        settings = load_settings()

        async def _run() -> list[dict[str, object]]:
            async with create_client(settings) as client:
                return await client.list_files()

        files = run_async(_run())
        typer.echo("filename\tpath\tmediaType\tsize")
        for file_info in files:
            typer.echo(
                "\t".join(
                    [
                        str(file_info.get("filename") or ""),
                        str(file_info.get("path") or ""),
                        str(file_info.get("mediaType") or ""),
                        str(file_info.get("size") or ""),
                    ]
                )
            )
    except (ValueError, RuntimeError) as exc:
        _fail(str(exc))


@app.command("import-cookies")
def import_cookies(
    input: Path = typer.Option(..., "--input"),
) -> None:
    try:
        destination, payload = import_cookies_to_session_cache(input)
        typer.echo(f"Cookies importados para {destination}")
        typer.echo(f"session_id: {payload['session_id']}")
        typer.echo(f"cookies: {len(payload['cookies'])}")
    except (ValueError, RuntimeError, FileNotFoundError, json.JSONDecodeError) as exc:
        _fail(str(exc))


@app.command()
def prompt(
    model: str | None = typer.Option(None, "--model"),
    prompt: str | None = typer.Option(None, "--prompt"),
    prompt_file: Path | None = typer.Option(None, "--prompt-file"),
    output: Path | None = typer.Option(None, "--output"),
    file: str | None = typer.Option(None, "--file"),
    session: str | None = typer.Option(None, "--session"),
    persona: str | None = typer.Option(
        None, "--persona", help="Nome ou slug da persona salva em ~/.adapta/persona/."
    ),
) -> None:
    try:
        settings = load_settings()
        model_key = _resolve_model(model, settings.adapta_model)
        persona_text: str | None = None
        if persona:
            persona_text = _load_persona_prompt_text(persona)
        request = build_prompt_request(
            model_key=model_key,
            prompt=prompt,
            prompt_file=prompt_file,
            output=output,
            files=_parse_file_option(file),
            session_id=session,
        )
        if persona_text:
            combined = f"{persona_text.rstrip()}\n\n{request.prompt_text}".strip()
            request = replace(request, prompt_text=combined)
        option = get_model_option(model_key)

        async def _run() -> tuple[str, str | None]:
            async with create_client(settings) as client:
                response = await execute_prompt(
                    client, request, model_backend=option.backend_name
                )
                persist_output(response.text, request.output_path)
                return response.text, response.session_id

        response_text, session_id = run_async(_run())
        if session_id:
            typer.echo(f"Prompt session_id: {session_id}")
        typer.echo(response_text)
    except (ValueError, RuntimeError) as exc:
        _fail(str(exc))


@app.command()
def persona(
    model: str | None = typer.Option(None, "--model"),
    input_file: Path | None = typer.Option(None, "--input-file"),
    update: bool = typer.Option(False, "--update"),
    list_existing: bool = typer.Option(
        False, "--list", help="Lista personas já salvas e retorna."
    ),
) -> None:
    try:
        if list_existing:
            _list_personas()
            return
        settings = load_settings()
        model_key = get_model_option(model or "claude").key
        answers, output_path, answers_path, overwrite = _resolve_persona_source(
            input_file=input_file,
            update=update,
        )
        if (output_path.exists() or answers_path.exists()) and not overwrite:
            typer.echo("Operação cancelada.")
            return

        questionnaire = build_persona_questionnaire(**answers)

        async def _run() -> tuple[str, str | None]:
            async with create_client(settings) as client:
                result = await generate_persona_document(
                    client,
                    questionnaire,
                    model_key=model_key,
                )
                save_persona_document(result.text, output_path, overwrite=overwrite)
                save_persona_answers(questionnaire, answers_path, overwrite=overwrite)
                return result.text, result.cleanup_warning

        _, cleanup_warning = run_async(_run())
        typer.echo(f"Resultado salvo em {output_path}")
        if cleanup_warning:
            typer.echo(cleanup_warning, err=True)
    except (ValueError, RuntimeError, FileExistsError) as exc:
        _fail(str(exc))


@app.command()
def chat(
    model: str | None = typer.Option(None, "--model"),
    file: str | None = typer.Option(None, "--file"),
) -> None:
    try:
        settings = load_settings()
        model_key = _resolve_model(model, settings.adapta_model)
        option = get_model_option(model_key)
        session = create_chat_session(model_key)
        file_paths = _parse_file_option(file)

        async def _run() -> None:
            async with create_client(settings) as client:
                try:
                    while True:
                        user_input = typer.prompt("Você")
                        if user_input.strip().lower() in {"exit", "quit", "sair"}:
                            break
                        response = await send_chat_message(
                            client,
                            session,
                            model_backend=option.backend_name,
                            prompt_text=user_input,
                            file_paths=file_paths,
                        )
                        typer.echo(response)
                finally:
                    try:
                        await close_chat_session(client, session)
                    except Exception as exc:  # noqa: BLE001
                        typer.echo(f"Falha ao limpar chat remoto: {exc}", err=True)

        run_async(_run())
    except (ValueError, RuntimeError) as exc:
        _fail(str(exc))


@app.command()
def debate(
    config: Path | None = typer.Option(None, "--config"),
    rounds: int | None = typer.Option(None, "--rounds"),
    output: Path | None = typer.Option(None, "--output"),
    prompt: str | None = typer.Option(None, "--prompt"),
    prompt_file: Path | None = typer.Option(None, "--prompt-file"),
    model_conclusion: str | None = typer.Option(None, "--model-conclusion"),
    file: str | None = typer.Option(None, "--file"),
    control: bool = typer.Option(False, "--control"),
) -> None:
    try:
        settings = load_settings()
        config_path, config_source = resolve_debate_config_path(config)

        if config_path is not None:
            agents = load_debate_agents(config_path)
        else:
            agent_count = _prompt_int("Número de agentes", minimum=2)
            agents = []
            for index in range(1, agent_count + 1):
                model_key = _select_model_interactively(f"Modelo do agente {index}")
                agent_prompt = typer.prompt(f"Prompt do agente {index}").strip()
                if not agent_prompt:
                    raise ValueError(f"O prompt do agente {index} não pode ser vazio.")
                agents.append(
                    DebateAgentConfig(
                        agent_id=f"A{index}",
                        model_key=model_key,
                        prompt=agent_prompt,
                    )
                )
            persist_debate_agents(agents, Path.cwd() / "debate.json")

        if rounds is None:
            rounds = _prompt_int("Número de rodadas", minimum=1)
        elif rounds < 1:
            raise ValueError("Informe um número de rodadas maior que zero.")

        debate_config = build_debate_config(
            agents=agents,
            rounds=rounds,
            topic_prompt=_resolve_debate_topic_prompt(prompt, prompt_file),
            conclusion_model_key=model_conclusion,
            output_path=output,
            config_source=config_source,
            file_paths=_parse_file_option(file),
        )

        def _emit_turn(turn) -> None:
            typer.echo(format_turn_label(turn))
            typer.echo(turn.response_text)
            typer.echo("")

        async def _run() -> tuple[str, Path | None, list[str]]:
            async with create_client(settings) as client:
                if control:
                    result = await run_controlled_debate(
                        client,
                        debate_config,
                        control_callback=_prompt_control_decision,
                        emit_turn=_emit_turn,
                    )
                else:
                    result = await run_debate(
                        client,
                        debate_config,
                        emit_turn=_emit_turn if output is None else None,
                    )
                return (
                    result.final_conclusion,
                    result.saved_path,
                    result.cleanup_warnings,
                )

        final_conclusion, saved_path, cleanup_warnings = run_async(_run())

        if output is None:
            typer.echo("Conclusão Final")
            typer.echo(final_conclusion)
        elif saved_path is not None:
            typer.echo(f"Resultado salvo em {saved_path}")

        for warning in cleanup_warnings:
            typer.echo(warning, err=True)
    except (ValueError, RuntimeError) as exc:
        _fail(str(exc))


@app.command()
def destilador(
    input: Path | None = typer.Option(None, "--input"),
    output: Path | None = typer.Option(None, "--output"),
    input_dir: Path | None = typer.Option(None, "--input-dir"),
    output_dir: Path | None = typer.Option(None, "--output-dir"),
    log: bool = typer.Option(False, "--log"),
) -> None:
    try:
        request = build_distillation_request(
            input_path=input,
            input_dir=input_dir,
            output_path=output,
            output_dir=output_dir,
        )
        settings = load_settings()

        def _progress(message: str) -> None:
            if log:
                typer.echo(message)

        async def _run() -> tuple[list[Path], list[str]]:
            async with create_client(settings) as client:
                result = await distill_documents(
                    client,
                    request,
                    progress_callback=_progress if log else None,
                )
                return result.final_output_paths, result.cleanup_warnings

        output_paths, cleanup_warnings = run_async(_run())
        for path in output_paths:
            typer.echo(f"Resultado salvo em {path}")
        for warning in cleanup_warnings:
            typer.echo(warning, err=True)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        _fail(str(exc))


@app.command()
def pipeline(
    input_dir: Path | None = typer.Option(None, "--input-dir"),
    output_dir: Path | None = typer.Option(None, "--output-dir"),
    db_path: Path | None = typer.Option(None, "--db-path"),
    mode: str = typer.Option("upload", "--mode"),
    job: int | None = typer.Option(None, "--job"),
    keep_chat: bool = typer.Option(False, "--keep-chat"),
    log: bool = typer.Option(False, "--log"),
) -> None:
    try:
        request = build_pipeline_request(
            input_dir=input_dir,
            output_dir=output_dir,
            db_path=db_path,
            mode=mode,
            job=job,
            keep_chat=keep_chat,
            log=log,
        )
        settings = load_settings()

        def _progress(message: str) -> None:
            if log:
                typer.echo(message)

        async def _run() -> tuple[list[Path], list[Path], list[str]]:
            async with create_client(settings) as client:
                result = await run_pipeline(
                    client,
                    request,
                    progress_callback=_progress if log else None,
                )
                return (
                    result.index_paths,
                    result.generated_documents,
                    result.cleanup_warnings,
                )

        index_paths, generated_documents, cleanup_warnings = run_async(_run())
        typer.echo(
            f"Pipeline concluído: {len(index_paths)} índice(s), {len(generated_documents)} documento(s) gerado(s)."
        )
        for path in index_paths:
            typer.echo(f"Índice salvo em {path}")
        for path in generated_documents:
            typer.echo(f"Documento salvo em {path}")
        for warning in cleanup_warnings:
            typer.echo(warning, err=True)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        _fail(str(exc))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
