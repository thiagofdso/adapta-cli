from __future__ import annotations

from pathlib import Path

from adapta.models import PromptRequest, ResponseArtifact


MAX_PROMPT_FILES = 5


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
    )


async def execute_prompt(
    client, request: PromptRequest, model_backend: str
) -> ResponseArtifact:
    if request.file_paths:
        files = [
            await client.upload_file(file_path) for file_path in request.file_paths
        ]
        text = await client.prompt_with_files(
            model_backend=model_backend,
            prompt=request.prompt_text,
            files=files,
        )
    else:
        text = await client.prompt(
            model_backend=model_backend, prompt=request.prompt_text
        )
    destination = "stdout" if request.output_path is None else "stdout+file"
    return ResponseArtifact(
        text=text, destination=destination, saved_path=request.output_path
    )
