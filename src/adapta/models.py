from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ModelOption:
    key: str
    display_name: str
    backend_name: str
    supports_chat: bool = True
    summary: str = ""


@dataclass(frozen=True)
class Settings:
    adapta_login: str
    adapta_password: str
    adapta_model: str | None
    env_file_path: Path
    data_dir: Path


@dataclass(frozen=True)
class PromptRequest:
    model_key: str
    prompt_text: str
    prompt_source: str
    output_path: Path | None
    file_paths: list[Path] = field(default_factory=list)
    session_id: str | None = None
    stream: bool = False
    folder_id: str | None = None


@dataclass
class ChatSession:
    chat_id: str
    model_key: str
    messages: list[dict[str, str]] = field(default_factory=list)
    cleanup_required: bool = False
    keep_chat: bool = False


@dataclass(frozen=True)
class ResponseArtifact:
    text: str
    destination: str
    saved_path: Path | None = None
    session_id: str | None = None


@dataclass(frozen=True)
class DebateAgentConfig:
    agent_id: str
    model_key: str
    prompt: str
    persona_path: Path | None = None


@dataclass(frozen=True)
class DebateConfig:
    agents: list[DebateAgentConfig]
    rounds: int
    topic_prompt: str
    conclusion_model_key: str
    output_path: Path | None
    config_source: str
    file_paths: list[Path] = field(default_factory=list)


@dataclass(frozen=True)
class DebateTurn:
    round_number: int
    agent_id: str
    model_key: str
    prompt_sent: str
    response_text: str
    status: str


@dataclass(frozen=True)
class DebateRound:
    round_number: int
    turns: list[DebateTurn]


@dataclass(frozen=True)
class DebateResult:
    config: DebateConfig
    rounds: list[DebateRound]
    final_conclusion: str
    saved_path: Path | None
    cleanup_warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DistillationRequest:
    input_path: Path | None
    input_dir_path: Path | None
    output_path: Path | None
    output_dir_path: Path | None
    mode: str
    upload_delay_seconds: float = 0.0


@dataclass(frozen=True)
class DistillationInputItem:
    source_path: Path
    target_output_path: Path
    source_origin: str


@dataclass(frozen=True)
class DistillationDimension:
    dimension_number: int
    prompt_text: str
    attempt_count: int
    selected_content: str
    status: str


@dataclass(frozen=True)
class DistillationArtifact:
    artifact_type: str
    path_or_identifier: str
    cleanup_required: bool
    preserved_reason: str | None = None


@dataclass(frozen=True)
class DistillationResult:
    request: DistillationRequest
    processed_items: list[DistillationInputItem]
    dimensions: list[DistillationDimension]
    final_output_paths: list[Path]
    cleanup_warnings: list[str] = field(default_factory=list)
    preserved_artifacts: list[DistillationArtifact] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineRequest:
    input_dir_path: Path
    output_dir_path: Path
    db_path: Path
    mode: str
    job_filter: int | None = None
    keep_chat: bool = False
    log_enabled: bool = False


@dataclass(frozen=True)
class PipelineDocument:
    source_path: Path
    source_name: str
    folder_path: Path
    relative_path: str
    file_type: str
    job_id: int | None = None
    stage_id: int = 1


@dataclass(frozen=True)
class PipelineArtifact:
    artifact_type: str
    artifact_path: Path
    document_source_path: Path | None = None


@dataclass(frozen=True)
class PipelineRunResult:
    request: PipelineRequest
    processed_files: list[PipelineDocument]
    index_paths: list[Path]
    generated_documents: list[Path]
    cleanup_warnings: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(frozen=True)
class SkillCreateRequest:
    input_dir_path: Path
    output_dir_path: Path
    db_path: Path
    job_filter: int | None = None
    keep_chat: bool = False
    log_enabled: bool = False


@dataclass(frozen=True)
class SkillDocument:
    source_path: Path
    source_name: str
    folder_path: Path
    relative_path: str
    file_type: str
    job_id: int | None = None
    stage_id: int = 1


@dataclass(frozen=True)
class SkillCreateRunResult:
    request: SkillCreateRequest
    processed_files: list[SkillDocument]
    index_paths: list[Path]
    generated_skills: list[Path]
    cleanup_warnings: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
