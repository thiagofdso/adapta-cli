from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any

from adapta.client import _generate_uuid7_like
from adapta.models import (
    DistillationArtifact,
    DistillationDimension,
    DistillationInputItem,
    DistillationRequest,
    DistillationResult,
)
from adapta.registry import get_model_option
from adapta.services.output_service import persist_output


DEFAULT_MODEL_KEY = "claude"
DISTILLATION_ITERATIONS = 2
DISTILLATION_RETRY_LIMIT = 3
DISTILLATION_RETRY_DELAY_SECONDS = 2.0
SUPPORTED_INPUT_SUFFIXES = {".pdf"}
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts" / "livro"


def build_distillation_request(
    *,
    input_path: Path | None,
    input_dir: Path | None,
    output_path: Path | None,
    output_dir: Path | None,
    upload_delay_seconds: float = 0.0,
) -> DistillationRequest:
    if input_path and input_dir:
        raise ValueError("Use apenas um modo de entrada por vez.")
    if output_path and output_dir:
        raise ValueError("Use apenas um modo de saída por vez.")

    if input_path:
        if output_path is None and output_dir is None:
            raise ValueError(
                "Informe --output ou --output-dir para o modo por arquivo."
            )
        if input_dir is not None:
            raise ValueError("Use apenas um modo de entrada por vez.")
        mode = "file"
    elif input_dir or output_dir:
        if output_path is not None:
            raise ValueError(
                "Use --input-dir com --output-dir para o modo por diretório."
            )
        if not input_dir or not output_dir:
            raise ValueError(
                "Informe --input-dir e --output-dir para o modo por diretório."
            )
        mode = "directory"
    else:
        raise ValueError("Informe --input e --output, ou --input-dir e --output-dir.")

    return DistillationRequest(
        input_path=input_path,
        input_dir_path=input_dir,
        output_path=output_path,
        output_dir_path=output_dir,
        mode=mode,
        upload_delay_seconds=max(0.0, upload_delay_seconds),
    )


def resolve_distillation_items(
    request: DistillationRequest,
) -> list[DistillationInputItem]:
    if request.mode == "file":
        assert request.input_path is not None
        _validate_input_file(request.input_path)
        if request.output_path is not None:
            target_output_path = request.output_path
        else:
            assert request.output_dir_path is not None
            request.output_dir_path.mkdir(parents=True, exist_ok=True)
            target_output_path = (
                request.output_dir_path / f"{request.input_path.stem}.md"
            )
        _validate_output_file(target_output_path)
        return [
            DistillationInputItem(
                source_path=request.input_path,
                target_output_path=target_output_path,
                source_origin="input-output-dir"
                if request.output_dir_path is not None
                else "input",
            )
        ]

    assert request.input_dir_path is not None
    assert request.output_dir_path is not None
    if not request.input_dir_path.exists() or not request.input_dir_path.is_dir():
        raise ValueError(
            f"Diretório de entrada não encontrado: {request.input_dir_path}"
        )
    request.output_dir_path.mkdir(parents=True, exist_ok=True)

    items = [
        DistillationInputItem(
            source_path=path,
            target_output_path=request.output_dir_path / f"{path.stem}.md",
            source_origin="input-dir",
        )
        for path in sorted(request.input_dir_path.iterdir())
        if path.is_file() and path.suffix.lower() in SUPPORTED_INPUT_SUFFIXES
    ]
    if not items:
        raise ValueError("Nenhum arquivo compatível encontrado em --input-dir.")
    for item in items:
        _validate_output_file(item.target_output_path)
    return items


async def distill_documents(
    client: Any,
    request: DistillationRequest,
    *,
    model_key: str = DEFAULT_MODEL_KEY,
    progress_callback: Any | None = None,
) -> DistillationResult:
    items = resolve_distillation_items(request)
    model_backend = get_model_option(model_key).backend_name
    all_dimensions: list[DistillationDimension] = []
    output_paths: list[Path] = []
    cleanup_warnings: list[str] = []
    preserved_artifacts: list[DistillationArtifact] = []

    for item in items:
        if progress_callback is not None:
            progress_callback(f"Processando {item.source_path.name}")
        item_result = await _distill_single_item(
            client,
            item,
            model_backend=model_backend,
            upload_delay_seconds=request.upload_delay_seconds,
            progress_callback=progress_callback,
        )
        all_dimensions.extend(item_result[0])
        output_paths.append(item_result[1])
        cleanup_warnings.extend(item_result[2])
        preserved_artifacts.extend(item_result[3])

    return DistillationResult(
        request=request,
        processed_items=items,
        dimensions=all_dimensions,
        final_output_paths=output_paths,
        cleanup_warnings=cleanup_warnings,
        preserved_artifacts=preserved_artifacts,
    )


def _validate_input_file(file_path: Path) -> None:
    if not file_path.exists() or not file_path.is_file():
        raise ValueError(f"Arquivo de entrada não encontrado: {file_path}")
    if file_path.suffix.lower() not in SUPPORTED_INPUT_SUFFIXES:
        raise ValueError(f"Arquivo de entrada incompatível: {file_path}")


def _validate_output_file(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)


def _load_dimension_prompt(dimension_number: int) -> str:
    prompt_path = PROMPTS_DIR / f"dimensao{dimension_number}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt da dimensão {dimension_number} não encontrado em {prompt_path}"
        )
    return prompt_path.read_text(encoding="utf-8")


def _build_dimension_messages(
    prompt_text: str, upload_info: dict[str, Any]
) -> list[dict[str, Any]]:
    file_part = {"type": "file", **upload_info}
    return [
        {"role": "user", "content": [{"type": "text", "text": prompt_text}, file_part]}
    ]


def _requires_processing_retry(response_text: str | None) -> bool:
    normalized = (response_text or "").lower()
    return (
        "nao consigo processar o arquivo" in normalized
        or "não consigo processar o arquivo" in normalized
    )


def _looks_like_empty_model_result(response_text: str | None) -> bool:
    normalized = (response_text or "").strip()
    return not normalized or normalized.startswith("ChatCompletionResult(")


def _remove_think_tags(text: str) -> str:
    return text.replace("<think>", "").replace("</think>", "").strip()


async def _run_dimension_once(
    client: Any,
    *,
    model_backend: str,
    prompt_text: str,
    upload_info: dict[str, Any],
) -> tuple[str, str]:
    chat_id = _generate_uuid7_like()
    if hasattr(client, "chat_with_files"):
        response = await client.chat_with_files(
            model_backend=model_backend,
            messages=[{"role": "user", "content": prompt_text}],
            chat_id=chat_id,
            files=[upload_info],
        )
    else:
        response = await client.chat(
            model_backend=model_backend,
            messages=_build_dimension_messages(prompt_text, upload_info),
            chat_id=chat_id,
        )
    return chat_id, _remove_think_tags(response)


async def _distill_single_item(
    client: Any,
    item: DistillationInputItem,
    *,
    model_backend: str,
    upload_delay_seconds: float,
    progress_callback: Any | None = None,
) -> tuple[list[DistillationDimension], Path, list[str], list[DistillationArtifact]]:
    working_dir = item.target_output_path.parent / item.source_path.stem
    working_dir.mkdir(parents=True, exist_ok=True)
    preserve_partials = item.source_origin == "input-output-dir"
    cleanup_warnings: list[str] = []
    preserved_artifacts: list[DistillationArtifact] = []
    chat_ids: list[str] = []
    upload_info = await client.upload_file(item.source_path)

    if upload_delay_seconds > 0:
        await asyncio.sleep(upload_delay_seconds)

    dimensions: list[DistillationDimension] = []
    dimension_files: list[Path] = []
    success = False
    try:
        for index in range(1, 8):
            prompt_text = _load_dimension_prompt(index)
            if progress_callback is not None:
                progress_callback(
                    f"Gerando dimensão {index} para {item.source_path.name}"
                )
            dim_file = working_dir / f"dimensao{index}.txt"
            best_content = ""
            selected_attempt = 0
            for attempt in range(1, DISTILLATION_RETRY_LIMIT + 1):
                results = await asyncio.gather(
                    *[
                        _run_dimension_once(
                            client,
                            model_backend=model_backend,
                            prompt_text=prompt_text,
                            upload_info=upload_info,
                        )
                        for _ in range(DISTILLATION_ITERATIONS)
                    ],
                    return_exceptions=True,
                )
                for result in results:
                    if isinstance(result, Exception):
                        continue
                    chat_id, content = result
                    chat_ids.append(chat_id)
                    if _requires_processing_retry(
                        content
                    ) or _looks_like_empty_model_result(content):
                        continue
                    if len(content) > len(best_content):
                        best_content = content
                        selected_attempt = attempt
                if best_content:
                    break
                if attempt < DISTILLATION_RETRY_LIMIT:
                    await asyncio.sleep(DISTILLATION_RETRY_DELAY_SECONDS)

            if not best_content:
                raise RuntimeError(f"Dimensão {index} sem respostas válidas")

            dim_file.write_text(
                best_content if best_content.endswith("\n") else f"{best_content}\n",
                encoding="utf-8",
            )
            dimension_files.append(dim_file)
            dimensions.append(
                DistillationDimension(
                    dimension_number=index,
                    prompt_text=prompt_text,
                    attempt_count=selected_attempt,
                    selected_content=best_content,
                    status="success",
                )
            )

        final_text = "\n\n".join(
            path.read_text(encoding="utf-8").strip() for path in dimension_files
        )
        persist_output(f"{final_text}\n", item.target_output_path)
        if progress_callback is not None:
            progress_callback(f"Consolidado salvo em {item.target_output_path}")
        success = True
        return (
            dimensions,
            item.target_output_path,
            cleanup_warnings,
            preserved_artifacts,
        )
    finally:
        if upload_info.get("path"):
            try:
                await client.delete_file(str(upload_info["path"]))
            except Exception as exc:  # noqa: BLE001
                cleanup_warnings.append(
                    f"Falha ao limpar arquivo remoto {upload_info['path']}: {exc}"
                )

        if chat_ids:
            try:
                await client.delete_chat(chat_ids)
            except Exception as exc:  # noqa: BLE001
                if "400 Bad Request" not in str(exc):
                    cleanup_warnings.append(f"Falha ao limpar chats remotos: {exc}")

        if success:
            if not preserve_partials:
                for dim_file in dimension_files:
                    try:
                        dim_file.unlink()
                    except FileNotFoundError:
                        pass
                    except Exception as exc:  # noqa: BLE001
                        cleanup_warnings.append(
                            f"Falha ao remover parcial {dim_file}: {exc}"
                        )
                try:
                    working_dir.rmdir()
                except OSError:
                    pass
        else:
            preserved_artifacts.append(
                DistillationArtifact(
                    artifact_type="working_dir",
                    path_or_identifier=str(working_dir),
                    cleanup_required=False,
                    preserved_reason="Falha ou interrupção durante a destilação via upload.",
                )
            )
