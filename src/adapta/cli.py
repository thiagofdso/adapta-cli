from __future__ import annotations

from pathlib import Path

import typer

from adapta.client import create_client
from adapta.config import load_settings
from adapta.logging import configure_logging
from adapta.registry import get_model_option, list_model_options, resolve_model_key
from adapta.runtime import run_async
from adapta.services.chat_service import (
    close_chat_session,
    create_chat_session,
    send_chat_message,
)
from adapta.services.output_service import persist_output
from adapta.services.prompt_service import build_prompt_request, execute_prompt


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


def _fail(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(code=1)


def _select_model_interactively() -> str:
    options = list_model_options()
    typer.echo("Selecione um modelo:")
    for index, option in enumerate(options, start=1):
        typer.echo(f"{index}. {option.display_name} ({option.key})")

    raw_choice = typer.prompt("Modelo")
    try:
        selected = options[int(raw_choice) - 1]
        return selected.key
    except (ValueError, IndexError):
        return get_model_option(raw_choice).key


def _resolve_model(explicit: str | None, default: str | None) -> str:
    if explicit or default:
        return resolve_model_key(explicit, default)
    return _select_model_interactively()


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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
