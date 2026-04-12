from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ModelOption:
    key: str
    display_name: str
    backend_name: str
    supports_chat: bool = True


@dataclass(frozen=True)
class Settings:
    adapta_login: str
    adapta_password: str
    adapta_model: str | None
    env_file_path: Path


@dataclass(frozen=True)
class PromptRequest:
    model_key: str
    prompt_text: str
    prompt_source: str
    output_path: Path | None


@dataclass
class ChatSession:
    chat_id: str
    model_key: str
    messages: list[dict[str, str]] = field(default_factory=list)
    cleanup_required: bool = False


@dataclass(frozen=True)
class ResponseArtifact:
    text: str
    destination: str
    saved_path: Path | None = None


@dataclass(frozen=True)
class DebateAgentConfig:
    agent_id: str
    model_key: str
    prompt: str


@dataclass(frozen=True)
class DebateConfig:
    agents: list[DebateAgentConfig]
    rounds: int
    topic_prompt: str
    conclusion_model_key: str
    output_path: Path | None
    config_source: str


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
