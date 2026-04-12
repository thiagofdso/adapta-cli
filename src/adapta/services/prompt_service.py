from __future__ import annotations

from pathlib import Path

from adapta.models import PromptRequest, ResponseArtifact


def build_prompt_request(
    model_key: str,
    prompt: str | None,
    prompt_file: Path | None,
    output: Path | None,
) -> PromptRequest:
    if bool(prompt) == bool(prompt_file):
        raise ValueError("Informe apenas uma origem de prompt.")

    if prompt_file is not None:
        content = prompt_file.read_text(encoding="utf-8").strip()
        if not content:
            raise ValueError("Arquivo de prompt vazio.")
        return PromptRequest(
            model_key=model_key,
            prompt_text=content,
            prompt_source="file",
            output_path=output,
        )

    normalized_prompt = (prompt or "").strip()
    if not normalized_prompt:
        raise ValueError("Prompt vazio.")
    return PromptRequest(
        model_key=model_key,
        prompt_text=normalized_prompt,
        prompt_source="inline",
        output_path=output,
    )


async def execute_prompt(
    client, request: PromptRequest, model_backend: str
) -> ResponseArtifact:
    text = await client.prompt(model_backend=model_backend, prompt=request.prompt_text)
    destination = "stdout" if request.output_path is None else "stdout+file"
    return ResponseArtifact(
        text=text, destination=destination, saved_path=request.output_path
    )
