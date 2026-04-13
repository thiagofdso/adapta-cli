from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

from adapta.models import Settings


PIPELINE_DB_ENV_VAR = "ADAPTA_PIPELINE_DB_PATH"


def default_env_file() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def default_pipeline_db_path() -> Path:
    return Path.home() / ".local" / "state" / "adapta-cli" / "pipeline.db"


def resolve_pipeline_db_path(db_path: Path | None = None) -> Path:
    if db_path is not None:
        return db_path.expanduser().resolve()

    env_value = os.environ.get(PIPELINE_DB_ENV_VAR)
    if env_value:
        return Path(env_value).expanduser().resolve()

    return default_pipeline_db_path().expanduser().resolve()


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
