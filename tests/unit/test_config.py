from pathlib import Path

from adapta.config import (
    DATA_DIR_ENV_VAR,
    default_data_dir,
    default_pipeline_db_path,
    default_skill_create_db_path,
    load_settings,
    resolve_pipeline_db_path,
    resolve_skill_create_db_path,
)


def test_resolve_pipeline_db_path_uses_default_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("ADAPTA_PIPELINE_DB_PATH", raising=False)

    resolved = resolve_pipeline_db_path()

    assert resolved == default_pipeline_db_path().expanduser().resolve()


def test_resolve_pipeline_db_path_uses_environment_when_set(
    monkeypatch, tmp_path: Path
) -> None:
    env_path = tmp_path / "env-pipeline.db"
    monkeypatch.setenv("ADAPTA_PIPELINE_DB_PATH", str(env_path))

    resolved = resolve_pipeline_db_path()

    assert resolved == env_path.resolve()


def test_resolve_pipeline_db_path_prefers_explicit_path(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ADAPTA_PIPELINE_DB_PATH", str(tmp_path / "env-pipeline.db"))
    explicit_path = tmp_path / "cli-pipeline.db"

    resolved = resolve_pipeline_db_path(explicit_path)

    assert resolved == explicit_path.resolve()


def test_resolve_skill_create_db_path_uses_default_when_unset(monkeypatch) -> None:
    monkeypatch.delenv("ADAPTA_SKILL_CREATE_DB_PATH", raising=False)

    resolved = resolve_skill_create_db_path()

    assert resolved == default_skill_create_db_path().expanduser().resolve()


def test_resolve_skill_create_db_path_uses_environment_when_set(
    monkeypatch, tmp_path: Path
) -> None:
    env_path = tmp_path / "skill-create.db"
    monkeypatch.setenv("ADAPTA_SKILL_CREATE_DB_PATH", str(env_path))

    resolved = resolve_skill_create_db_path()

    assert resolved == env_path.resolve()


def test_resolve_skill_create_db_path_prefers_explicit_path(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("ADAPTA_SKILL_CREATE_DB_PATH", str(tmp_path / "env.db"))
    explicit_path = tmp_path / "cli.db"

    resolved = resolve_skill_create_db_path(explicit_path)

    assert resolved == explicit_path.resolve()


def test_load_settings_uses_default_data_dir(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ADAPTA_LOGIN=user\nADAPTA_PASSWORD=pass\n")
    monkeypatch.delenv(DATA_DIR_ENV_VAR, raising=False)

    settings = load_settings(env_file)

    assert settings.data_dir == default_data_dir()


def test_load_settings_uses_custom_data_dir(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("ADAPTA_LOGIN=user\nADAPTA_PASSWORD=pass\n")
    custom_dir = tmp_path / "custom_data"
    monkeypatch.setenv(DATA_DIR_ENV_VAR, str(custom_dir))

    settings = load_settings(env_file)

    assert settings.data_dir == custom_dir.resolve()
