from pathlib import Path

from adapta.config import default_pipeline_db_path, resolve_pipeline_db_path


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
