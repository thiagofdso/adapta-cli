from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values

from adapta.models import Settings


PIPELINE_DB_ENV_VAR = "ADAPTA_PIPELINE_DB_PATH"
SKILL_CREATE_DB_ENV_VAR = "ADAPTA_SKILL_CREATE_DB_PATH"
DATA_DIR_ENV_VAR = "ADAPTA_DATA_DIR"


def default_env_file() -> Path:
    return Path(__file__).resolve().parents[2] / ".env"


def default_data_dir() -> Path:
    return Path.home() / ".adapta"


def default_pipeline_db_path(data_dir: Path | None = None) -> Path:
    base = data_dir or default_data_dir()
    return base / "state" / "pipeline.db"


def default_skill_create_db_path(data_dir: Path | None = None) -> Path:
    base = data_dir or default_data_dir()
    return base / "state" / "skill-create.db"


def resolve_pipeline_db_path(
    db_path: Path | None = None, data_dir: Path | None = None
) -> Path:
    if db_path is not None:
        return db_path.expanduser().resolve()

    env_value = os.environ.get(PIPELINE_DB_ENV_VAR)
    if env_value:
        return Path(env_value).expanduser().resolve()

    return default_pipeline_db_path(data_dir).expanduser().resolve()


def resolve_skill_create_db_path(
    db_path: Path | None = None, data_dir: Path | None = None
) -> Path:
    if db_path is not None:
        return db_path.expanduser().resolve()

    env_value = os.environ.get(SKILL_CREATE_DB_ENV_VAR)
    if env_value:
        return Path(env_value).expanduser().resolve()

    return default_skill_create_db_path(data_dir).expanduser().resolve()


def load_settings(env_file: Path | None = None) -> Settings:
    resolved_env_file = env_file or default_env_file()
    values = {**dotenv_values(resolved_env_file), **os.environ}

    login = values.get("ADAPTA_LOGIN")
    password = values.get("ADAPTA_PASSWORD")
    model = values.get("ADAPTA_MODEL") or None
    data_dir_raw = values.get(DATA_DIR_ENV_VAR)

    if not login or not password:
        raise ValueError("ADAPTA_LOGIN e ADAPTA_PASSWORD são obrigatórios.")

    data_dir = (
        Path(data_dir_raw).expanduser().resolve()
        if data_dir_raw
        else default_data_dir()
    )

    return Settings(
        adapta_login=str(login),
        adapta_password=str(password),
        adapta_model=str(model) if model else None,
        env_file_path=resolved_env_file,
        data_dir=data_dir,
    )
