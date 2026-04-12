from __future__ import annotations
from pathlib import Path

import typer

from adapta.client import create_client
from adapta.config import load_settings
from adapta.logging import configure_logging
from adapta.models import DebateAgentConfig
from adapta.registry import get_model_option, list_model_options, resolve_model_key
from adapta.runtime import run_async
from adapta.services.chat_service import (
    close_chat_session,
    create_chat_session,
    send_chat_message,
)
from adapta.services.debate_service import (
    build_debate_config,
    format_turn_label,
    load_debate_agents,
    persist_debate_agents,
    resolve_debate_config_path,
    run_debate,
)
from adapta.services.output_service import persist_output
from adapta.services.prompt_service import build_prompt_request, execute_prompt


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


@app.command()
def models() -> None:
    for option in list_model_options():
        typer.echo(f"{option.key}\t{option.display_name}\t{option.backend_name}")


@app.callback()
def callback(log: str | None = typer.Option(None, "--log")) -> None:
    configure_logging(log)


@app.command()
def prompt(
    model: str | None = typer.Option(None, "--model"),
    prompt: str | None = typer.Option(None, "--prompt"),
    prompt_file: Path | None = typer.Option(None, "--prompt-file"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    try:
        settings = load_settings()
        model_key = _resolve_model(model, settings.adapta_model)
        request = build_prompt_request(
            model_key=model_key, prompt=prompt, prompt_file=prompt_file, output=output
        )
        option = get_model_option(model_key)

        async def _run() -> str:
            async with create_client(settings) as client:
                response = await execute_prompt(
                    client, request, model_backend=option.backend_name
                )
                persist_output(response.text, request.output_path)
                return response.text

        typer.echo(run_async(_run()))
    except (ValueError, RuntimeError) as exc:
        _fail(str(exc))


@app.command()
def chat(model: str | None = typer.Option(None, "--model")) -> None:
    try:
        settings = load_settings()
        model_key = _resolve_model(model, settings.adapta_model)
        option = get_model_option(model_key)
        session = create_chat_session(model_key)

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
    model_conclusion: str | None = typer.Option(None, "--model-conclusion"),
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
            topic_prompt=(prompt or ""),
            conclusion_model_key=model_conclusion,
            output_path=output,
            config_source=config_source,
        )

        def _emit_turn(turn) -> None:
            typer.echo(format_turn_label(turn))
            typer.echo(turn.response_text)
            typer.echo("")

        async def _run() -> tuple[str, Path | None, list[str]]:
            async with create_client(settings) as client:
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
