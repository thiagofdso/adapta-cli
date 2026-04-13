# Data Model: Comando pipeline por diretório

## PipelineRequest

- `input_dir_path: Path`
- `output_dir_path: Path`
- `db_path: Path`
- `mode: str`
- `job_filter: int | None`
- `keep_chat: bool`
- `log_enabled: bool`

Validation rules:

- `input_dir_path` deve existir e ser diretório legível.
- `output_dir_path` deve ser utilizável para criação e escrita.
- `db_path` deve apontar para um arquivo SQLite gravável ou criável.
- `mode` deve aceitar apenas valores compatíveis com o pipeline legado exposto pela CLI.

## PipelineRun

- `run_id: str`
- `input_dir_path: Path`
- `output_dir_path: Path`
- `db_path: Path`
- `started_at: datetime`
- `finished_at: datetime | None`
- `status: str`
- `processed_count: int`
- `failed_count: int`
- `cleanup_warnings: list[str]`

State transitions:

- `pending` -> `running`
- `running` -> `completed`
- `running` -> `completed_with_warnings`
- `running` -> `failed`

## PipelineDocument

- `source_path: Path`
- `source_name: str`
- `folder_path: Path`
- `relative_path: str`
- `file_type: str`
- `status: str`
- `job_id: int | None`

Validation rules:

- apenas extensões compatíveis com o pipeline original podem virar documentos elegíveis.
- `relative_path` deve ser determinístico para rastrear colisões de nome.

State transitions:

- `discovered` -> `queued`
- `queued` -> `indexed`
- `indexed` -> `knowledge_generated`
- `knowledge_generated` -> `cleaned`
- qualquer estado -> `failed`

## PipelineDatabaseConfig

- `cli_value: Path | None`
- `env_value: Path | None`
- `default_value: Path`
- `resolved_value: Path`
- `resolution_source: str`

Validation rules:

- `resolved_value` deve seguir precedência fixa: CLI, ambiente, padrão.
- `resolution_source` deve ser um de `cli`, `environment`, `default`.

## PipelineJobRecord

- `id: int`
- `file_path: str`
- `file_name: str`
- `folder_path: str`
- `stage_id: int`
- `status_id: int`
- `created_at: datetime`

Notes:

- Esta entidade preserva a forma operacional do banco legado para rastrear processamento por arquivo.

## PipelineKnowledgeRecord

- `id: int`
- `name: str`
- `description: str | None`
- `position: int | None`
- `folder_path: str`
- `status_id: int`
- `created_at: datetime`
- `files: list[str]`

Validation rules:

- `folder_path` é obrigatório.
- `files` deve manter nomes únicos por conhecimento.

## PipelineArtifact

- `artifact_type: str`
- `artifact_path: Path`
- `document_source_path: Path | None`
- `cleanup_required: bool`
- `preserved_reason: str | None`

Artifact types expected:

- `index-json`
- `index-part-json`
- `docs-markdown`
- `chat-log`
- `sqlite-db`

## Relationships

- Um `PipelineRun` resolve um `PipelineDatabaseConfig`.
- Um `PipelineRun` descobre muitos `PipelineDocument`.
- Um `PipelineDocument` pode originar um `PipelineJobRecord`.
- Um `PipelineJobRecord` pode gerar muitos `PipelineKnowledgeRecord`.
- Um `PipelineDocument` pode gerar muitos `PipelineArtifact`.
- Um `PipelineRun` agrega os `PipelineArtifact` produzidos durante a execução.
