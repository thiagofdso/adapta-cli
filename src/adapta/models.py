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
