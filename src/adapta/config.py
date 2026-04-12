from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

from adapta.models import Settings


def default_env_file() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def load_settings(env_file: Path | None = None) -> Settings:
    resolved_env_file = env_file or default_env_file()
    values = {**dotenv_values(resolved_env_file), **os.environ}

    login = values.get("ADAPTA_LOGIN")
    password = values.get("ADAPTA_PASSWORD")
    model = values.get("ADAPTA_MODEL") or None

    if not login or not password:
        raise ValueError("ADAPTA_LOGIN e ADAPTA_PASSWORD são obrigatórios.")

    return Settings(
        adapta_login=str(login),
        adapta_password=str(password),
        adapta_model=str(model) if model else None,
        env_file_path=resolved_env_file,
    )
