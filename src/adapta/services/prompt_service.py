from __future__ import annotations

import logging
from pathlib import Path

from adapta.models import PromptRequest, ResponseArtifact
from adapta.services.chat_service import generate_chat_id


MAX_PROMPT_FILES = 5
logger = logging.getLogger(__name__)


def normalize_file_paths(files: list[Path] | None) -> list[Path]:
    if not files:
        return []
    normalized = [path for path in files if str(path).strip()]
    if not normalized or len(normalized) > MAX_PROMPT_FILES:
        raise ValueError("Informe entre 1 e 5 arquivos em --file.")
    missing = next(
        (path for path in normalized if not path.exists() or not path.is_file()), None
    )
    if missing is not None:
        raise ValueError(f"Arquivo não encontrado: {missing}")
    return normalized


def build_prompt_request(
    model_key: str,
    prompt: str | None,
    prompt_file: Path | None,
    output: Path | None,
    files: list[Path] | None,
    session_id: str | None = None,
    stream: bool = False,
    debug_stream: bool = False,
    folder_id: str | None = None,
    keep_chat: bool = False,
) -> PromptRequest:
    if bool(prompt) == bool(prompt_file):
        raise ValueError("Informe apenas uma origem de prompt.")

    file_paths = normalize_file_paths(files)

    if prompt_file is not None:
        content = prompt_file.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError("Arquivo de prompt vazio.")
        return PromptRequest(
            model_key=model_key,
            prompt_text=content,
            prompt_source="file",
            output_path=output,
            file_paths=file_paths,
            session_id=(session_id or None),
            stream=stream,
            debug_stream=debug_stream,
            folder_id=folder_id,
            keep_chat=keep_chat,
        )

    normalized_prompt = (prompt or "").strip()
    if not normalized_prompt:
        raise ValueError("Prompt vazio.")
    return PromptRequest(
        model_key=model_key,
        prompt_text=normalized_prompt,
        prompt_source="inline",
        output_path=output,
        file_paths=file_paths,
        session_id=(session_id or None),
        stream=stream,
        debug_stream=debug_stream,
        folder_id=folder_id,
        keep_chat=keep_chat,
    )


async def execute_prompt(
    client,
    request: PromptRequest,
    model_backend: str,
    context_ids: list[str] | None = None,
    expert_id: str | None = None,
    settings=None,
) -> ResponseArtifact:
    session_id = request.session_id or generate_chat_id()
    messages = [{"role": "user", "content": request.prompt_text}]

    if request.stream:
        files = None
        if request.file_paths:
            files = [
                await client.upload_file(file_path) for file_path in request.file_paths
            ]

        async def _consume_stream(current_messages: list[dict[str, str]], current_chat_id: str) -> str:
            chunks: list[str] = []
            async for event_type, payload in client.chat_stream(
                model_backend=model_backend,
                messages=current_messages,
                chat_id=current_chat_id,
                files=files,
                folder_id=request.folder_id,
                context_ids=context_ids,
                expert_id=expert_id,
                search_workaround=(settings.adapta_search_workaround if settings else None),
                search_continue_prompt=(settings.adapta_search_continue_prompt if settings else None),
                search_max_workarounds=(settings.adapta_search_max_workarounds if settings else 1),
            ):
                if request.debug_stream:
                    print(
                        f"\n[stream-event] type={event_type} payload={payload!r}",
                        flush=True,
                    )
                if event_type == "answer" and payload:
                    print(payload, end="", flush=True)
                    chunks.append(payload)
            print(flush=True)
            return "".join(chunks)

        text = await _consume_stream(messages, session_id)
    else:
        if request.file_paths:
            files = [
                await client.upload_file(file_path) for file_path in request.file_paths
            ]
            text = await client.chat_with_files(
                model_backend=model_backend,
                messages=messages,
                chat_id=session_id,
                files=files,
                folder_id=request.folder_id,
                context_ids=context_ids,
                expert_id=expert_id,
            )
        else:
            text = await client.chat(
                model_backend=model_backend,
                messages=messages,
                chat_id=session_id,
                folder_id=request.folder_id,
                context_ids=context_ids,
                expert_id=expert_id,
            )

    destination = "stdout" if request.output_path is None else "stdout+file"
    return ResponseArtifact(
        text=text,
        destination=destination,
        saved_path=request.output_path,
        session_id=session_id,
    )


async def _delete_ephemeral_chat(client, chat_id: str) -> None:
    delete_chat = getattr(client, "delete_chat", None)
    if delete_chat is None:
        return
    try:
        await delete_chat(chat_id)
    except Exception:
        logger.warning("Falha ao remover o chat %s", chat_id, exc_info=True)
