from __future__ import annotations

import asyncio
import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from adapta.config import resolve_pipeline_db_path
from adapta.models import (
    PipelineDocument,
    PipelineRequest,
    PipelineRunResult,
)
from adapta.registry import get_model_option


DEFAULT_PIPELINE_MODEL_KEY = "claude"
PIPELINE_STAGE2_CONCURRENCY = 3
SUPPORTED_PIPELINE_SUFFIXES = {".pdf", ".txt"}
PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts" / "pipeline"


def build_pipeline_request(
    *,
    input_dir: Path | None,
    output_dir: Path | None,
    db_path: Path | None,
    mode: str,
    job: int | None,
    keep_chat: bool,
    log: bool,
) -> PipelineRequest:
    if input_dir is None or output_dir is None:
        raise ValueError("Informe --input-dir e --output-dir para o comando pipeline.")

    resolved_input = input_dir.expanduser().resolve()
    resolved_output = output_dir.expanduser().resolve()
    resolved_mode = (mode or "upload").strip().lower()

    if resolved_mode not in {"upload", "docling"}:
        raise ValueError("Informe um valor válido para --mode: upload ou docling.")
    if not resolved_input.exists() or not resolved_input.is_dir():
        raise ValueError(f"Diretório de entrada não encontrado: {resolved_input}")

    resolved_output.mkdir(parents=True, exist_ok=True)
    resolved_db_path = resolve_pipeline_db_path(db_path)
    resolved_db_path.parent.mkdir(parents=True, exist_ok=True)

    return PipelineRequest(
        input_dir_path=resolved_input,
        output_dir_path=resolved_output,
        db_path=resolved_db_path,
        mode=resolved_mode,
        job_filter=job,
        keep_chat=keep_chat,
        log_enabled=log,
    )


def discover_pipeline_documents(request: PipelineRequest) -> list[PipelineDocument]:
    documents: list[PipelineDocument] = []
    for path in sorted(request.input_dir_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_PIPELINE_SUFFIXES:
            continue
        folder_path = path.parent.resolve()
        relative_path = str(path.resolve().relative_to(request.input_dir_path))
        documents.append(
            PipelineDocument(
                source_path=path.resolve(),
                source_name=path.name,
                folder_path=folder_path,
                relative_path=relative_path,
                file_type=path.suffix.lower(),
            )
        )
    if not documents:
        raise ValueError("Nenhum arquivo compatível encontrado em --input-dir.")
    return documents


async def run_pipeline(
    client: Any,
    request: PipelineRequest,
    *,
    progress_callback: Any | None = None,
    model_key: str = DEFAULT_PIPELINE_MODEL_KEY,
) -> PipelineRunResult:
    if request.mode == "docling":
        raise RuntimeError(
            "Modo docling ainda não está disponível nesta CLI. Use --mode upload."
        )

    started_at = datetime.now(UTC)
    documents = discover_pipeline_documents(request)
    model_backend = get_model_option(model_key).backend_name
    cleanup_warnings: list[str] = []

    with _connect_db(request.db_path) as connection:
        _initialize_database(connection)
        documents = _register_documents(connection, documents)
        selected_documents = _filter_documents_by_job(
            connection, documents, request.job_filter
        )
        if not selected_documents:
            raise ValueError(
                "Job informado não encontrado para os arquivos descobertos."
            )

        grouped = _group_documents_by_folder(selected_documents)
        index_paths: list[Path] = []
        generated_documents: list[Path] = []

        for folder_path, folder_documents in grouped.items():
            if progress_callback is not None:
                progress_callback(f"Indexando {folder_path.name}")
            index_path = await _run_stage1_for_folder(
                client,
                connection,
                request,
                folder_path=folder_path,
                documents=folder_documents,
                model_backend=model_backend,
                cleanup_warnings=cleanup_warnings,
                progress_callback=progress_callback,
            )
            index_paths.append(index_path)

            if progress_callback is not None:
                progress_callback(f"Gerando markdowns de {folder_path.name}")
            generated_documents.extend(
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

    return PipelineRunResult(
        request=request,
        processed_files=selected_documents,
        index_paths=index_paths,
        generated_documents=generated_documents,
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
        CREATE TABLE IF NOT EXISTS knowledges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        CREATE TABLE IF NOT EXISTS files_knowledges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id INTEGER NOT NULL,
            file_name TEXT NOT NULL,
            UNIQUE(knowledge_id, file_name),
            FOREIGN KEY (knowledge_id) REFERENCES knowledges (id)
        )
        """
    )
    connection.commit()


def _register_documents(
    connection: sqlite3.Connection, documents: list[PipelineDocument]
) -> list[PipelineDocument]:
    registered: list[PipelineDocument] = []
    cursor = connection.cursor()
    for document in documents:
        cursor.execute(
            "SELECT id FROM jobs WHERE file_path = ?", (str(document.source_path),)
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO jobs (file_path, file_name, folder_path, stage_id, status_id) VALUES (?, ?, ?, ?, ?)",
                (
                    str(document.source_path),
                    document.source_name,
                    str(document.folder_path),
                    1,
                    1,
                ),
            )
            job_id = int(cursor.lastrowid)
        else:
            job_id = int(row["id"])
        registered.append(replace(document, job_id=job_id))
    connection.commit()
    return registered


def _filter_documents_by_job(
    connection: sqlite3.Connection,
    documents: list[PipelineDocument],
    job_filter: int | None,
) -> list[PipelineDocument]:
    if job_filter is None:
        return documents
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = ?", (job_filter,))
    if cursor.fetchone() is None:
        return []
    return [document for document in documents if document.job_id == job_filter]


def _group_documents_by_folder(
    documents: list[PipelineDocument],
) -> dict[Path, list[PipelineDocument]]:
    grouped: dict[Path, list[PipelineDocument]] = defaultdict(list)
    for document in documents:
        grouped[document.folder_path].append(document)
    return dict(sorted(grouped.items(), key=lambda item: str(item[0]).lower()))


async def _run_stage1_for_folder(
    client: Any,
    connection: sqlite3.Connection,
    request: PipelineRequest,
    *,
    folder_path: Path,
    documents: list[PipelineDocument],
    model_backend: str,
    cleanup_warnings: list[str],
    progress_callback: Any | None,
) -> Path:
    index_path = _index_path_for_folder(request, folder_path)
    existing_entries = _load_index_data(index_path)

    for document in documents:
        if progress_callback is not None:
            progress_callback(f"Processando {document.source_name}")
        prompt = _build_extraction_prompt(document.source_name, existing_entries)
        prompt, upload_infos = await _prepare_prompt_and_uploads(
            client, prompt, [document.source_path]
        )
        try:
            raw_text = await _call_pipeline_prompt(
                client,
                model_backend=model_backend,
                prompt=prompt,
                upload_infos=upload_infos,
            )
        finally:
            for upload_info in upload_infos:
                await _cleanup_remote_upload(client, upload_info, cleanup_warnings)

        extracted_entries = _parse_knowledge_json(
            raw_text, current_file_name=document.source_name
        )
        existing_entries = _merge_knowledge_entries(existing_entries, extracted_entries)
        _save_index_data(index_path, existing_entries)
        _upsert_knowledges(connection, str(folder_path), existing_entries)
        _update_job_state(connection, document.job_id, stage_id=2, status_id=3)

    return index_path


async def _run_stage2_for_folder(
    client: Any,
    connection: sqlite3.Connection,
    request: PipelineRequest,
    *,
    folder_path: Path,
    model_backend: str,
    cleanup_warnings: list[str],
    progress_callback: Any | None,
) -> list[Path]:
    generated_paths: list[Path] = []
    knowledges = _get_pending_knowledges(connection, str(folder_path))
    if not knowledges:
        return generated_paths

    index_json = json.dumps(
        {"knowledges": _load_index_data(_index_path_for_folder(request, folder_path))},
        ensure_ascii=False,
        indent=2,
    )
    docs_dir = _docs_dir_for_folder(request, folder_path)
    docs_dir.mkdir(parents=True, exist_ok=True)
    semaphore = asyncio.Semaphore(
        max(1, min(PIPELINE_STAGE2_CONCURRENCY, len(knowledges)))
    )

    async def _generate_knowledge_markdown(
        knowledge: sqlite3.Row,
    ) -> tuple[int, Path, str, list[str]]:
        async with semaphore:
            if progress_callback is not None:
                progress_callback(f"Gerando conhecimento {knowledge['name']}")
            file_names = _get_files_for_knowledge(connection, int(knowledge["id"]))
            source_paths = _resolve_source_paths(folder_path, file_names)
            prompt = _build_creation_prompt(
                knowledge_name=str(knowledge["name"]),
                index_knowledge=index_json,
            )
            prompt, upload_infos = await _prepare_prompt_and_uploads(
                client, prompt, source_paths
            )
            local_cleanup_warnings: list[str] = []
            try:
                markdown = await _call_pipeline_prompt(
                    client,
                    model_backend=model_backend,
                    prompt=prompt,
                    upload_infos=upload_infos,
                )
            finally:
                for upload_info in upload_infos:
                    await _cleanup_remote_upload(
                        client, upload_info, local_cleanup_warnings
                    )

            output_path = docs_dir / f"{_sanitize_filename(str(knowledge['name']))}.md"
            return int(knowledge["id"]), output_path, markdown, local_cleanup_warnings

    knowledge_results = await asyncio.gather(
        *[_generate_knowledge_markdown(knowledge) for knowledge in knowledges]
    )
    for knowledge_id, output_path, markdown, local_cleanup_warnings in knowledge_results:
        output_path.write_text(_strip_markdown_fences(markdown), encoding="utf-8")
        generated_paths.append(output_path)
        cleanup_warnings.extend(local_cleanup_warnings)
        _update_knowledge_status(connection, knowledge_id, status_id=3)

    return generated_paths


def _build_extraction_prompt(
    current_file_name: str, existing_entries: list[dict[str, Any]]
) -> str:
    template = _load_prompt_template("knowledge_extraction.txt")
    index_listing = "- nenhum (primeira execucao)"
    bounds_info = (
        "The current index is empty; append new knowledges in the returned JSON."
    )
    if existing_entries:
        index_listing = "- index.json"
        bounds_info = (
            f"The current index contains {len(existing_entries)} knowledges. "
            "Return a full JSON object with the merged result."
        )
    return (
        template.replace("{current_file}", current_file_name)
        .replace("{current_index_files}", index_listing)
        .replace("{index_bounds_info}", bounds_info)
    )


def _build_creation_prompt(*, knowledge_name: str, index_knowledge: str) -> str:
    template = _load_prompt_template("knowledge_creation.txt")
    return template.replace("{knowledge_name}", knowledge_name).replace(
        "{index_knowledge}", index_knowledge
    )


async def _call_pipeline_prompt(
    client: Any,
    *,
    model_backend: str,
    prompt: str,
    upload_infos: list[dict[str, Any]],
) -> str:
    if upload_infos:
        return await client.prompt_with_files(
            model_backend=model_backend,
            prompt=prompt,
            files=upload_infos,
        )
    return await client.prompt(model_backend=model_backend, prompt=prompt)


async def _prepare_prompt_and_uploads(
    client: Any, prompt: str, source_paths: list[Path]
) -> tuple[str, list[dict[str, Any]]]:
    inline_blocks: list[str] = []
    upload_infos: list[dict[str, Any]] = []
    for source_path in source_paths:
        if source_path.suffix.lower() == ".txt":
            inline_blocks.append(_build_inline_text_block(source_path))
        else:
            upload_infos.append(await client.upload_file(source_path))

    final_prompt = prompt
    if inline_blocks:
        final_prompt = f"{prompt}\n\n# ARQUIVOS TXT INLINE\n\n" + "\n\n".join(
            inline_blocks
        )
    return final_prompt, upload_infos


def _build_inline_text_block(source_path: Path) -> str:
    source_text = source_path.read_text(encoding="utf-8", errors="replace").strip()
    return f"Arquivo: {source_path.name}\n```text\n{source_text}\n```"


def _load_prompt_template(file_name: str) -> str:
    prompt_path = PROMPTS_DIR / file_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt do pipeline não encontrado: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _index_path_for_folder(request: PipelineRequest, folder_path: Path) -> Path:
    root_slug = _slugify(request.input_dir_path.name or "entrada")
    relative_parts = []
    try:
        relative = folder_path.resolve().relative_to(request.input_dir_path)
        relative_parts = [_slugify(part) for part in relative.parts if _slugify(part)]
    except ValueError:
        relative_parts = [_slugify(folder_path.name)]

    parts = [root_slug] + [
        part for part in relative_parts if part and part != root_slug
    ]
    file_name = "_".join(parts) if parts else root_slug
    indexes_dir = request.output_dir_path / "indexes"
    indexes_dir.mkdir(parents=True, exist_ok=True)
    return indexes_dir / f"{file_name}.json"


def _docs_dir_for_folder(request: PipelineRequest, folder_path: Path) -> Path:
    root_slug = _slugify(request.input_dir_path.name or "conteudo")
    docs_root = request.output_dir_path / f"docs_{root_slug}"
    try:
        relative = folder_path.resolve().relative_to(request.input_dir_path)
    except ValueError:
        return docs_root
    if not relative.parts:
        return docs_root
    return docs_root.joinpath(*relative.parts)


def _load_index_data(index_path: Path) -> list[dict[str, Any]]:
    if not index_path.exists():
        return []
    raw = json.loads(index_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("knowledges"), list):
        return []
    return [_sanitize_knowledge_entry(entry) for entry in raw.get("knowledges") or []]


def _save_index_data(index_path: Path, entries: list[dict[str, Any]]) -> None:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps({"knowledges": entries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse_knowledge_json(
    raw_text: str, *, current_file_name: str
) -> list[dict[str, Any]]:
    normalized = _extract_json_object(_strip_code_fences(raw_text))
    try:
        data = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Falha ao interpretar JSON do pipeline: {exc}") from exc
    knowledges = data.get("knowledges") if isinstance(data, dict) else None
    if not isinstance(knowledges, list):
        raise RuntimeError("Resposta do pipeline não contém a chave 'knowledges'.")
    return [_sanitize_knowledge_entry(entry, current_file_name) for entry in knowledges]


def _merge_knowledge_entries(
    existing_entries: list[dict[str, Any]], new_entries: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    merged = [dict(entry) for entry in existing_entries]
    position_by_name = {
        str(entry.get("name") or "").strip().lower(): index
        for index, entry in enumerate(merged)
    }
    for entry in new_entries:
        key = str(entry.get("name") or "").strip().lower()
        if not key:
            continue
        if key in position_by_name:
            current = merged[position_by_name[key]]
            current_files = _normalize_files(current.get("files") or [])
            new_files = _normalize_files(entry.get("files") or [])
            current["files"] = _normalize_files(current_files + new_files)
            if not current.get("description") and entry.get("description"):
                current["description"] = entry.get("description")
        else:
            position_by_name[key] = len(merged)
            merged.append(_sanitize_knowledge_entry(entry))
    return merged


def _sanitize_knowledge_entry(
    entry: dict[str, Any] | Any, current_file_name: str | None = None
) -> dict[str, Any]:
    raw = entry if isinstance(entry, dict) else {}
    files = _normalize_files(list(raw.get("files") or []))
    if current_file_name and current_file_name not in files:
        files = _normalize_files(files + [current_file_name])
    return {
        "name": str(raw.get("name") or "").strip(),
        "description": str(raw.get("description") or "").strip(),
        "files": files,
    }


def _normalize_files(file_names: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for item in file_names:
        clean = str(item or "").strip()
        if clean and clean not in seen:
            normalized.append(clean)
            seen.add(clean)
        if len(normalized) >= 5:
            break
    return normalized


def _upsert_knowledges(
    connection: sqlite3.Connection, folder_path: str, entries: list[dict[str, Any]]
) -> None:
    cursor = connection.cursor()
    for position, entry in enumerate(entries, start=1):
        cursor.execute(
            "SELECT id FROM knowledges WHERE name = ? AND folder_path = ?",
            (entry["name"], folder_path),
        )
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO knowledges (name, description, position, folder_path, status_id) VALUES (?, ?, ?, ?, ?)",
                (entry["name"], entry["description"], position, folder_path, 1),
            )
            knowledge_id = int(cursor.lastrowid)
        else:
            knowledge_id = int(row["id"])
            cursor.execute(
                "UPDATE knowledges SET description = ?, position = ? WHERE id = ?",
                (entry["description"], position, knowledge_id),
            )
        cursor.execute(
            "DELETE FROM files_knowledges WHERE knowledge_id = ?", (knowledge_id,)
        )
        cursor.executemany(
            "INSERT OR IGNORE INTO files_knowledges (knowledge_id, file_name) VALUES (?, ?)",
            [(knowledge_id, file_name) for file_name in entry["files"]],
        )
    connection.commit()


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


def _get_pending_knowledges(
    connection: sqlite3.Connection, folder_path: str
) -> list[sqlite3.Row]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM knowledges WHERE folder_path = ? AND status_id = 1 ORDER BY COALESCE(position, id)",
        (folder_path,),
    )
    return list(cursor.fetchall())


def _get_files_for_knowledge(
    connection: sqlite3.Connection, knowledge_id: int
) -> list[str]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT file_name FROM files_knowledges WHERE knowledge_id = ? ORDER BY file_name",
        (knowledge_id,),
    )
    return [str(row["file_name"]) for row in cursor.fetchall()]


def _resolve_source_paths(folder_path: Path, file_names: list[str]) -> list[Path]:
    source_paths = [
        folder_path / file_name
        for file_name in file_names
        if (folder_path / file_name).exists()
    ]
    if not source_paths:
        raise RuntimeError(
            f"Nenhum arquivo fonte encontrado para a pasta {folder_path}"
        )
    return source_paths[:5]


def _update_knowledge_status(
    connection: sqlite3.Connection, knowledge_id: int, *, status_id: int
) -> None:
    connection.execute(
        "UPDATE knowledges SET status_id = ? WHERE id = ?",
        (status_id, knowledge_id),
    )
    connection.commit()


def _finalize_folder_jobs(connection: sqlite3.Connection, folder_path: str) -> None:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT COUNT(*) AS pending_count FROM knowledges WHERE folder_path = ? AND status_id != 3",
        (folder_path,),
    )
    row = cursor.fetchone()
    if row is not None and int(row["pending_count"] or 0) == 0:
        connection.execute(
            "UPDATE jobs SET stage_id = 3, status_id = 3 WHERE folder_path = ?",
            (folder_path,),
        )
        connection.commit()


async def _cleanup_remote_upload(
    client: Any, upload_info: dict[str, Any], cleanup_warnings: list[str]
) -> None:
    upload_path = upload_info.get("path")
    if not upload_path:
        return
    try:
        await client.delete_file(str(upload_path))
    except Exception as exc:  # noqa: BLE001
        cleanup_warnings.append(f"Falha ao limpar upload remoto {upload_path}: {exc}")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    return normalized.strip("-") or "conteudo"


def _sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[\\/:*?\"<>|]", "", value).strip().rstrip(". ")
    return sanitized or "conhecimento"


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```[a-zA-Z0-9_-]*\n", "", stripped)
        stripped = re.sub(r"\n```$", "", stripped)
    return stripped.strip()


def _strip_markdown_fences(text: str) -> str:
    stripped = _strip_code_fences(text)
    return stripped if stripped.endswith("\n") else f"{stripped}\n"


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return text
    return text[start : end + 1]
