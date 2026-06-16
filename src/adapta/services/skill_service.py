from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from adapta.config import resolve_skill_create_db_path
from adapta.models import SkillCreateRequest, SkillCreateRunResult, SkillDocument
from adapta.registry import get_model_option
from adapta.services.chat_service import create_chat_session
from adapta.services.pipeline_service import (
    DEFAULT_PIPELINE_MODEL_KEY,
    PROMPTS_DIR,
    _extract_json_object,
    _strip_code_fences,
    _strip_markdown_fences,
)


SKILL_STAGE2_CONCURRENCY = 3
SUPPORTED_SKILL_SUFFIXES = {".txt", ".md"}


def build_skill_create_request(
    *,
    input_dir: Path | None,
    output_dir: Path | None,
    db_path: Path | None,
    job: int | None,
    keep_chat: bool,
    log: bool,
    max_retries: int = 3,
    retry_delay_seconds: float = 60.0,
) -> SkillCreateRequest:
    if input_dir is None or output_dir is None:
        raise ValueError("Informe --input-dir e --output-dir para o comando skill-create.")

    resolved_input = input_dir.expanduser().resolve()
    resolved_output = output_dir.expanduser().resolve()
    if not resolved_input.exists() or not resolved_input.is_dir():
        raise ValueError(f"Diretório de entrada não encontrado: {resolved_input}")

    resolved_output.mkdir(parents=True, exist_ok=True)
    resolved_db_path = resolve_skill_create_db_path(db_path)
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    return SkillCreateRequest(
        input_dir_path=resolved_input,
        output_dir_path=resolved_output,
        db_path=resolved_db_path,
        job_filter=job,
        keep_chat=keep_chat,
        log_enabled=log,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
    )


def discover_skill_documents(request: SkillCreateRequest) -> list[SkillDocument]:
    documents: list[SkillDocument] = []
    for path in sorted(request.input_dir_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SKILL_SUFFIXES:
            continue
        folder_path = path.parent.resolve()
        documents.append(
            SkillDocument(
                source_path=path.resolve(),
                source_name=path.name,
                folder_path=folder_path,
                relative_path=str(path.resolve().relative_to(request.input_dir_path)),
                file_type=path.suffix.lower(),
            )
        )
    if not documents:
        raise ValueError("Nenhum arquivo compatível encontrado em --input-dir.")
    return documents


async def run_skill_create(
    client: Any,
    request: SkillCreateRequest,
    *,
    progress_callback: Any | None = None,
    model_key: str = DEFAULT_PIPELINE_MODEL_KEY,
) -> SkillCreateRunResult:
    started_at = datetime.now(UTC)
    documents = discover_skill_documents(request)
    model_backend = get_model_option(model_key).backend_name
    cleanup_warnings: list[str] = []

    with _connect_db(request.db_path) as connection:
        _initialize_database(connection)
        documents = _register_documents(connection, documents)
        selected_documents = _filter_documents_by_job(
            connection, documents, request.job_filter
        )
        if not selected_documents:
            raise ValueError("Job informado não encontrado para os arquivos descobertos.")

        index_paths: list[Path] = []
        generated_skills: list[Path] = []
        for folder_path, folder_documents in _group_documents_by_folder(
            selected_documents
        ).items():
            if progress_callback is not None:
                progress_callback(f"Indexando {folder_path.name}")
            index_path = await _run_stage1_for_folder(
                client,
                connection,
                request,
                folder_path=folder_path,
                documents=folder_documents,
                model_backend=model_backend,
                progress_callback=progress_callback,
            )
            index_paths.append(index_path)

            if progress_callback is not None:
                progress_callback(f"Gerando skills de {folder_path.name}")
            generated_skills.extend(
                await _run_stage2_for_folder(
                    client,
                    connection,
                    request,
                    folder_path=folder_path,
                    model_backend=model_backend,
                    cleanup_warnings=cleanup_warnings,
                    progress_callback=progress_callback,
                )
            )
            _finalize_folder_jobs(connection, str(folder_path))

    return SkillCreateRunResult(
        request=request,
        processed_files=selected_documents,
        index_paths=index_paths,
        generated_skills=generated_skills,
        cleanup_warnings=cleanup_warnings,
        started_at=started_at,
        finished_at=datetime.now(UTC),
    )


def _connect_db(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def _initialize_database(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            file_name TEXT NOT NULL,
            folder_path TEXT NOT NULL,
            stage_id INTEGER NOT NULL,
            status_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_key TEXT,
            name TEXT NOT NULL,
            description TEXT,
            position INTEGER,
            folder_path TEXT NOT NULL,
            status_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, folder_path)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            contribution TEXT,
            UNIQUE(skill_id, file_name),
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
        """
    )
    _ensure_column(connection, "skills", "skill_key", "TEXT")
    connection.commit()


def _register_documents(
    connection: sqlite3.Connection, documents: list[SkillDocument]
) -> list[SkillDocument]:
    registered: list[SkillDocument] = []
    cursor = connection.cursor()
    for document in documents:
        cursor.execute(
            "SELECT id, stage_id FROM jobs WHERE file_path = ?",
            (str(document.source_path),),
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO jobs (file_path, file_name, folder_path, stage_id, status_id) VALUES (?, ?, ?, ?, ?)",
                (str(document.source_path), document.source_name, str(document.folder_path), 1, 1),
            )
            job_id = int(cursor.lastrowid)
            stage_id = 1
        else:
            job_id = int(row["id"])
            stage_id = int(row["stage_id"])
        registered.append(replace(document, job_id=job_id, stage_id=stage_id))
    connection.commit()
    return registered


def _filter_documents_by_job(
    connection: sqlite3.Connection,
    documents: list[SkillDocument],
    job_filter: int | None,
) -> list[SkillDocument]:
    if job_filter is None:
        return documents
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = ?", (job_filter,))
    if cursor.fetchone() is None:
        return []
    return [document for document in documents if document.job_id == job_filter]


def _group_documents_by_folder(
    documents: list[SkillDocument],
) -> dict[Path, list[SkillDocument]]:
    grouped: dict[Path, list[SkillDocument]] = defaultdict(list)
    for document in documents:
        grouped[document.folder_path].append(document)
    return dict(sorted(grouped.items(), key=lambda item: str(item[0]).lower()))


async def _run_stage1_for_folder(
    client: Any,
    connection: sqlite3.Connection,
    request: SkillCreateRequest,
    *,
    folder_path: Path,
    documents: list[SkillDocument],
    model_backend: str,
    progress_callback: Any | None,
) -> Path:
    index_path = _index_path_for_folder(request, folder_path)
    existing_entries = _load_index_data(index_path)

    for document in documents:
        if document.stage_id >= 2:
            if progress_callback is not None:
                progress_callback(f"Ignorando (já indexado): {document.source_name}")
            continue

        if progress_callback is not None:
            progress_callback(f"Processando {document.source_name}")
        prompt = _build_extraction_prompt(document.source_name, existing_entries)
        prompt = _append_inline_blocks(prompt, [document.source_path])

        merged_entries = None
        max_attempts = request.max_retries
        for attempt in range(1, max_attempts + 1):
            try:
                _validate_skill_entries(existing_entries)
                raw_text = await _call_skill_prompt(
                    client,
                    model_backend=model_backend,
                    prompt=prompt,
                    keep_chat=request.keep_chat,
                )
                extracted_entries = _parse_skill_json(
                    raw_text, current_file_name=document.source_name
                )
                _validate_skill_entries(extracted_entries)
                attempted_merge = _merge_skill_entries(existing_entries, extracted_entries)
                _validate_skill_entries(attempted_merge)
                merged_entries = attempted_merge
                break
            except (httpx.HTTPError, RuntimeError, ValueError) as exc:
                if attempt >= max_attempts:
                    raise
                if progress_callback is not None:
                    progress_callback(
                        f"Aviso: falha na tentativa {attempt} para {document.source_name}. Retentando... ({exc})"
                    )
                await asyncio.sleep(request.retry_delay_seconds)

        if merged_entries is not None:
            existing_entries = merged_entries
            _save_index_data(index_path, existing_entries)
            _upsert_skills(connection, str(folder_path), existing_entries)
        _update_job_state(connection, document.job_id, stage_id=2, status_id=3)

    return index_path


async def _run_stage2_for_folder(
    client: Any,
    connection: sqlite3.Connection,
    request: SkillCreateRequest,
    *,
    folder_path: Path,
    model_backend: str,
    cleanup_warnings: list[str],
    progress_callback: Any | None,
) -> list[Path]:
    generated_paths: list[Path] = []
    if progress_callback is not None:
        for skill in _get_completed_skills(connection, str(folder_path)):
            progress_callback(f"Ignorando (já gerado): {skill['name']}")

    skills = _get_pending_skills(connection, str(folder_path))
    if not skills:
        return generated_paths

    index_json = json.dumps(
        {"skills": _load_index_data(_index_path_for_folder(request, folder_path))},
        ensure_ascii=False,
        indent=2,
    )
    semaphore = asyncio.Semaphore(max(1, min(SKILL_STAGE2_CONCURRENCY, len(skills))))

    async def _generate_skill_markdown(skill: sqlite3.Row) -> None:
        async with semaphore:
            if progress_callback is not None:
                progress_callback(f"Gerando skill {skill['name']}")
            file_names = _get_files_for_skill(connection, int(skill["id"]))
            source_paths = _resolve_source_paths(folder_path, file_names)
            prompt = _build_creation_prompt(
                skill_name=str(skill["name"]),
                index_knowledge=index_json,
            )
            prompt = _append_inline_blocks(prompt, source_paths)
            markdown = await _call_skill_creation_prompt(
                client,
                model_backend=model_backend,
                prompt=prompt,
                keep_chat=request.keep_chat,
            )
            cleaned_markdown = _validate_skill_markdown(markdown)
            skill_dir = _skills_dir_for_folder(request, folder_path) / _skill_dir_name(
                cleaned_markdown, str(skill["name"])
            )
            skill_dir.mkdir(parents=True, exist_ok=True)
            output_path = skill_dir / "SKILL.md"
            output_path.write_text(cleaned_markdown, encoding="utf-8")
            generated_paths.append(output_path)
            _update_skill_status(connection, int(skill["id"]), status_id=3)

    skill_results = await asyncio.gather(
        *[_generate_skill_markdown(skill) for skill in skills],
        return_exceptions=True,
    )
    for skill, result in zip(skills, skill_results, strict=True):
        if isinstance(result, Exception):
            raise RuntimeError(
                f"Erro na geração de skill {skill['name']}: {result}"
            ) from result

    return generated_paths


def _build_extraction_prompt(
    current_file_name: str, existing_entries: list[dict[str, Any]]
) -> str:
    template = _load_prompt_template("skill_extraction_plain.txt")
    index_listing = "- nenhum (primeira execucao)"
    bounds_info = "The current index is empty; append new skills in the returned JSON."
    if existing_entries:
        index_listing = "- index.json"
        bounds_info = (
            f"The current index contains {len(existing_entries)} skills. "
            "Return a full JSON object with the merged result."
        )
    return (
        template.replace("{current_file}", current_file_name)
        .replace("{current_index_files}", index_listing)
        .replace("{index_bounds_info}", bounds_info)
    )


def _build_creation_prompt(*, skill_name: str, index_knowledge: str) -> str:
    template = _load_prompt_template("skill_creation_plain.txt")
    return template.replace("{skill_name}", skill_name).replace(
        "{index_knowledge}", index_knowledge
    )


async def _call_skill_creation_prompt(
    client: Any, *, model_backend: str, prompt: str, keep_chat: bool
) -> str:
    if callable(getattr(client, "chat", None)):
        return await _call_skill_creation_chat(
            client,
            model_backend=model_backend,
            prompt=prompt,
            keep_chat=keep_chat,
        )

    markdown = await _call_skill_prompt(
        client,
        model_backend=model_backend,
        prompt=prompt,
        keep_chat=keep_chat,
    )
    try:
        return _validate_skill_markdown(markdown)
    except RuntimeError as exc:
        correction_prompt = _build_skill_correction_prompt(markdown, str(exc))
        corrected_markdown = await _call_skill_prompt(
            client,
            model_backend=model_backend,
            prompt=correction_prompt,
            keep_chat=keep_chat,
        )
        return _validate_skill_markdown(corrected_markdown)


async def _call_skill_creation_chat(
    client: Any, *, model_backend: str, prompt: str, keep_chat: bool
) -> str:
    session = create_chat_session("skill-create")
    cleanup_required = False
    try:
        session.messages.append({"role": "user", "content": prompt})
        markdown = await client.chat(
            model_backend=model_backend,
            messages=session.messages,
            chat_id=session.chat_id,
        )
        cleanup_required = True
        session.messages.append({"role": "assistant", "content": markdown})
        try:
            return _validate_skill_markdown(markdown)
        except RuntimeError as exc:
            session.messages.append(
                {
                    "role": "user",
                    "content": _build_skill_correction_prompt(markdown, str(exc)),
                }
            )
            corrected_markdown = await client.chat(
                model_backend=model_backend,
                messages=session.messages,
                chat_id=session.chat_id,
            )
            return _validate_skill_markdown(corrected_markdown)
    finally:
        if cleanup_required and not keep_chat and callable(getattr(client, "delete_chat", None)):
            await client.delete_chat(session.chat_id)


async def _call_skill_prompt(
    client: Any, *, model_backend: str, prompt: str, keep_chat: bool
) -> str:
    return await client.prompt(
        model_backend=model_backend,
        prompt=prompt,
        keep_chat=keep_chat,
    )


def _build_skill_correction_prompt(invalid_markdown: str, validation_error: str) -> str:
    return f"""A resposta anterior nao seguiu o formato obrigatorio de SKILL.md.

Erro de validacao: {validation_error}

Corrija a resposta anterior e devolva SOMENTE o conteudo final do arquivo SKILL.md.

# REGRAS NEGATIVAS OBRIGATORIAS
* Nao escreva introducao, comentario, explicacao, diagnostico ou frase como "Com base no material".
* Nao use markdown fences como ```markdown ou ```.
* Nao inclua objetos, reprs ou wrappers como ChatCompletionResult(...).
* Nao inclua texto antes do frontmatter YAML.
* Nao inclua texto depois da ultima secao do template.
* Nao altere a estrutura de secoes do template.
* Nao deixe placeholders entre colchetes.

# FORMATO OBRIGATORIO
---
name: nome-da-skill-em-hyphen-case
description: >
  Descricao curta do que a skill faz e quando usar.
---

# Nome Da Skill

## 🎯 Categoria
Metodo

## 📌 Descricao
...

## 📝 Instrucoes
...

## ⚡ Passo a Passo
...

## 💡 Exemplos de Aplicacao
...

## ⚠️ Pontos de Atencao
...

## 🔧 Recursos Necessarios
...

## Consideracoes
...

# RESPOSTA ANTERIOR INVALIDA
{invalid_markdown}
"""


def _append_inline_blocks(prompt: str, source_paths: list[Path]) -> str:
    return f"{prompt}\n\n# ARQUIVOS INLINE\n\n" + "\n\n".join(
        _build_inline_text_block(source_path) for source_path in source_paths
    )


def _build_inline_text_block(source_path: Path) -> str:
    source_text = source_path.read_text(encoding="utf-8", errors="replace").strip()
    return f"Arquivo: {source_path.name}\n```text\n{source_text}\n```"


def _load_prompt_template(file_name: str) -> str:
    prompt_path = PROMPTS_DIR / file_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt de skill não encontrado: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _validate_skill_markdown(markdown: str) -> str:
    cleaned = _normalize_model_text(markdown)
    if not cleaned or cleaned.startswith("ChatCompletionResult("):
        raise RuntimeError("Resposta da skill vazia ou wrapper de resultado inválido.")
    if not cleaned.startswith("---\n"):
        raise RuntimeError("Resposta contém comentários ou markdown fences antes do SKILL.md.")

    frontmatter_match = re.match(r"^---\n(.*?)\n---\n+", cleaned, re.DOTALL)
    if frontmatter_match is None:
        raise RuntimeError("Header YAML da skill ausente ou fora do padrão.")

    frontmatter = frontmatter_match.group(1)
    name_match = re.search(r"^name:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*$", frontmatter, re.MULTILINE)
    if name_match is None:
        raise RuntimeError("Header YAML deve conter name em hyphen-case.")
    if re.search(r"^description:\s*>\s*$", frontmatter, re.MULTILINE) is None:
        raise RuntimeError("Header YAML deve conter description: >.")

    description_lines = _frontmatter_description_lines(frontmatter)
    if not any(line.strip() for line in description_lines):
        raise RuntimeError("Header YAML deve conter descrição não vazia.")

    required_headings = [
        "# ",
        "## 🎯 Categoria",
        "## 📌 Descricao",
        "## 📝 Instrucoes",
        "## ⚡ Passo a Passo",
        "## 💡 Exemplos de Aplicacao",
        "## ⚠️ Pontos de Atencao",
        "## 🔧 Recursos Necessarios",
        "## Consideracoes",
    ]
    cursor = frontmatter_match.end()
    for heading in required_headings:
        found_at = cleaned.find(heading, cursor)
        if found_at == -1:
            raise RuntimeError(f"Resposta da skill não contém a seção obrigatória: {heading}")
        cursor = found_at + len(heading)

    if re.search(r"^\s*Com base no|^\s*Aqui est[áa]|^\s*Segue", cleaned, re.IGNORECASE | re.MULTILINE):
        raise RuntimeError("Resposta contém comentários ou texto introdutório.")
    if re.search(r"^\s*\[[^\]\n]+\]\s*$", cleaned, re.MULTILINE):
        raise RuntimeError("Resposta contém placeholders entre colchetes.")

    return cleaned if cleaned.endswith("\n") else f"{cleaned}\n"


def _normalize_model_text(markdown: Any) -> str:
    if isinstance(markdown, str):
        return markdown.strip()
    messages = getattr(markdown, "messages", None)
    if isinstance(messages, list):
        answers = [
            str(entry.get("text", ""))
            for entry in messages
            if isinstance(entry, dict) and entry.get("kind") == "answer"
        ]
        if any(answer.strip() for answer in answers):
            return "".join(answers).strip()
    return str(markdown).strip()


def _frontmatter_description_lines(frontmatter: str) -> list[str]:
    lines = frontmatter.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^description:\s*>\s*$", line):
            collected: list[str] = []
            for candidate in lines[index + 1 :]:
                if candidate.startswith(" ") or candidate.startswith("\t"):
                    collected.append(candidate)
                    continue
                break
            return collected
    return []


def _index_path_for_folder(request: SkillCreateRequest, folder_path: Path) -> Path:
    root_slug = _slugify(request.input_dir_path.name or "entrada")
    relative_parts = []
    try:
        relative = folder_path.resolve().relative_to(request.input_dir_path)
        relative_parts = [_slugify(part) for part in relative.parts if _slugify(part)]
    except ValueError:
        relative_parts = [_slugify(folder_path.name)]

    parts = [root_slug] + [part for part in relative_parts if part and part != root_slug]
    file_name = "_".join(parts) if parts else root_slug
    indexes_dir = request.output_dir_path / "indexes"
    indexes_dir.mkdir(parents=True, exist_ok=True)
    return indexes_dir / f"{file_name}.json"


def _skills_dir_for_folder(request: SkillCreateRequest, folder_path: Path) -> Path:
    root_slug = _slugify(request.input_dir_path.name or "conteudo")
    skills_root = request.output_dir_path / f"skills_{root_slug}"
    try:
        relative = folder_path.resolve().relative_to(request.input_dir_path)
    except ValueError:
        return skills_root
    if not relative.parts:
        return skills_root
    return skills_root.joinpath(*relative.parts)


def _load_index_data(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Falha ao interpretar JSON de origem ({index_path}): {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("skills"), list):
        raise RuntimeError(
            f"Formato inválido no JSON de origem ({index_path}): esperado um objeto com a chave 'skills'."
        )
    entries = _merge_skill_entries([], raw.get("skills") or [])
    _validate_skill_entries(entries)
    return entries


def _save_index_data(index_path: Path, entries: list[dict[str, Any]]) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"skills": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse_skill_json(raw_text: str, *, current_file_name: str) -> list[dict[str, Any]]:
    normalized = _extract_json_object(_strip_code_fences(raw_text))
    try:
        data = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Falha ao interpretar JSON do skill-create: {exc}") from exc
    skills = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(skills, list):
        raise RuntimeError("Resposta do skill-create não contém a chave 'skills'.")
    return [_sanitize_skill_entry(entry, current_file_name) for entry in skills]


def _validate_skill_entries(entries: list[dict[str, Any]]) -> None:
    if not isinstance(entries, list):
        raise RuntimeError("As entradas de skill devem ser uma lista.")
    seen_names: dict[str, str] = {}
    for index, entry in enumerate(entries):
        skill_id = str(entry.get("id") or "").strip()
        if not skill_id:
            raise RuntimeError(f"Entrada na posição {index} não possui um 'id' válido.")
        name = str(entry.get("name") or "").strip()
        if not name:
            raise RuntimeError(f"Entrada na posição {index} não possui um 'name' válido.")
        normalized_name = _normalized_skill_name(name)
        if normalized_name in seen_names:
            raise RuntimeError(
                f"Nome de skill duplicado no índice: '{name}' conflita com '{seen_names[normalized_name]}'."
            )
        seen_names[normalized_name] = name
        description = str(entry.get("description") or "").strip()
        if not description:
            raise RuntimeError(f"Entrada '{name}' não possui uma 'description' válida.")
        files = entry.get("files")
        if not isinstance(files, list) or not files:
            raise RuntimeError(f"Entrada '{name}' não possui arquivos associados ('files').")
        for file_entry in files:
            if (
                not isinstance(file_entry, dict)
                or not str(file_entry.get("name") or "").strip()
            ):
                raise RuntimeError(f"Entrada '{name}' possui arquivo inválido.")


def _merge_skill_entries(
    existing_entries: list[dict[str, Any]], new_entries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged = [_sanitize_skill_entry(entry) for entry in existing_entries]
    position_by_id: dict[str, int] = {}
    position_by_name: dict[str, int] = {}
    for index, entry in enumerate(merged):
        skill_id = str(entry.get("id") or "").strip().lower()
        if skill_id:
            position_by_id[f"id:{skill_id}"] = index
        normalized_name = _normalized_skill_name(str(entry.get("name") or ""))
        if normalized_name:
            position_by_name[f"name:{normalized_name}"] = index

    for entry in new_entries:
        sanitized_entry = _sanitize_skill_entry(entry)
        id_key = _entry_patch_key(sanitized_entry)
        name_key = f"name:{_normalized_skill_name(str(sanitized_entry.get('name') or ''))}"
        position = position_by_id.get(id_key)
        if position is None:
            position = position_by_name.get(name_key)
        if position is not None:
            current = merged[position]
            position_by_id[id_key] = position
            if name_key != "name:":
                position_by_name[name_key] = position
            current["files"] = _normalize_files(
                list(current.get("files") or [])
                + list(sanitized_entry.get("files") or [])
            )
            if sanitized_entry.get("description"):
                current["description"] = sanitized_entry["description"]
        else:
            position = len(merged)
            position_by_id[id_key] = position
            if name_key != "name:":
                position_by_name[name_key] = position
            merged.append(sanitized_entry)
    return merged


def _sanitize_skill_entry(
    entry: dict[str, Any] | Any, current_file_name: str | None = None
) -> dict[str, Any]:
    raw = entry if isinstance(entry, dict) else {}
    files = _normalize_files(list(raw.get("files") or []))
    if current_file_name and current_file_name not in {
        str(file_entry.get("name") or "") for file_entry in files
    }:
        files = _normalize_files(
            files + [{"name": current_file_name, "contribution": "Arquivo atual"}]
        )

    name = str(raw.get("name") or "").strip()
    name = "".join(char for char in name if char.isalnum() or char.isspace())
    name = re.sub(r"\s+", " ", name).strip()
    skill_id = _slugify(str(raw.get("id") or "").strip() or name)

    return {
        "id": skill_id,
        "name": name,
        "description": str(raw.get("description") or "").strip(),
        "files": files,
    }


def _normalized_skill_name(name: str) -> str:
    decomposed = unicodedata.normalize("NFKD", str(name or ""))
    ascii_name = "".join(char for char in decomposed if not unicodedata.combining(char))
    ascii_name = "".join(char for char in ascii_name if char.isalnum() or char.isspace())
    return re.sub(r"\s+", " ", ascii_name).strip().casefold()


def _entry_patch_key(entry: dict[str, Any]) -> str:
    skill_id = str(entry.get("id") or "").strip()
    if skill_id:
        return f"id:{skill_id.lower()}"
    return f"name:{_normalized_skill_name(str(entry.get('name') or ''))}"


def _normalize_files(files: list[Any]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in files:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            contribution = str(item.get("contribution") or "").strip()
        else:
            name = str(item or "").strip()
            contribution = ""
        if name and name not in seen:
            normalized.append({"name": name, "contribution": contribution})
            seen.add(name)
        if len(normalized) >= 5:
            break
    return normalized


def _upsert_skills(
    connection: sqlite3.Connection, folder_path: str, entries: list[dict[str, Any]]
) -> None:
    cursor = connection.cursor()
    for position, entry in enumerate(entries, start=1):
        cursor.execute(
            "SELECT id FROM skills WHERE skill_key = ? AND folder_path = ?",
            (entry["id"], folder_path),
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                """
                SELECT id FROM skills
                WHERE name = ? AND folder_path = ?
                """,
                (entry["name"], folder_path),
            )
            row = cursor.fetchone()
        if row is None:
            cursor.execute(
                """
                INSERT INTO skills
                    (skill_key, name, description, position, folder_path, status_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["id"],
                    entry["name"],
                    entry["description"],
                    position,
                    folder_path,
                    1,
                ),
            )
            skill_id = int(cursor.lastrowid)
        else:
            skill_id = int(row["id"])
            cursor.execute(
                """
                UPDATE skills
                SET skill_key = ?, name = ?, description = ?, position = ?
                WHERE id = ?
                """,
                (entry["id"], entry["name"], entry["description"], position, skill_id),
            )
        cursor.execute("DELETE FROM files_skills WHERE skill_id = ?", (skill_id,))
        cursor.executemany(
            "INSERT OR IGNORE INTO files_skills (skill_id, file_name, contribution) VALUES (?, ?, ?)",
            [
                (skill_id, file_entry["name"], file_entry.get("contribution", ""))
                for file_entry in entry["files"]
            ],
        )
    connection.commit()


def _ensure_column(
    connection: sqlite3.Connection, table_name: str, column_name: str, column_type: str
) -> None:
    cursor = connection.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = {str(row["name"]) for row in cursor.fetchall()}
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _update_job_state(
    connection: sqlite3.Connection, job_id: int | None, *, stage_id: int, status_id: int
) -> None:
    if job_id is None:
        return
    connection.execute(
        "UPDATE jobs SET stage_id = ?, status_id = ? WHERE id = ?",
        (stage_id, status_id, job_id),
    )
    connection.commit()


def _get_pending_skills(connection: sqlite3.Connection, folder_path: str) -> list[sqlite3.Row]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM skills WHERE folder_path = ? AND status_id = 1 ORDER BY COALESCE(position, id)",
        (folder_path,),
    )
    return list(cursor.fetchall())


def _get_completed_skills(
    connection: sqlite3.Connection, folder_path: str
) -> list[sqlite3.Row]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM skills WHERE folder_path = ? AND status_id = 3 ORDER BY COALESCE(position, id)",
        (folder_path,),
    )
    return list(cursor.fetchall())


def _get_files_for_skill(connection: sqlite3.Connection, skill_id: int) -> list[str]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT file_name FROM files_skills WHERE skill_id = ? ORDER BY file_name",
        (skill_id,),
    )
    return [str(row["file_name"]) for row in cursor.fetchall()]


def _resolve_source_paths(folder_path: Path, file_names: list[str]) -> list[Path]:
    source_paths = [
        folder_path / file_name
        for file_name in file_names
        if (folder_path / file_name).exists()
    ]
    if not source_paths:
        raise RuntimeError(f"Nenhum arquivo fonte encontrado para a pasta {folder_path}")
    return source_paths[:5]


def _update_skill_status(
    connection: sqlite3.Connection, skill_id: int, *, status_id: int
) -> None:
    connection.execute(
        "UPDATE skills SET status_id = ? WHERE id = ?",
        (status_id, skill_id),
    )
    connection.commit()


def _finalize_folder_jobs(connection: sqlite3.Connection, folder_path: str) -> None:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS pending_count FROM skills WHERE folder_path = ? AND status_id != 3",
        (folder_path,),
    )
    row = cursor.fetchone()
    if row is not None and int(row["pending_count"] or 0) == 0:
        connection.execute(
            "UPDATE jobs SET stage_id = 3, status_id = 3 WHERE folder_path = ?",
            (folder_path,),
        )
        connection.commit()


def _skill_dir_name(markdown: str, fallback_name: str) -> str:
    frontmatter_match = re.match(r"\s*---\s*\n(.*?)\n---", markdown, re.DOTALL)
    if frontmatter_match:
        for line in frontmatter_match.group(1).splitlines():
            if line.strip().startswith("name:"):
                value = line.split(":", 1)[1].strip()
                if value:
                    return _slugify(value)
    return _slugify(fallback_name)


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "skill"
