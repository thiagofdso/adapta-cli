from pathlib import Path

import pytest

from adapta.config import Settings, load_settings


def test_load_settings_reads_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        'ADAPTA_LOGIN="user@example.com"\nADAPTA_PASSWORD="secret"\nADAPTA_MODEL="gpt"\n',
        encoding="utf-8",
    )

    settings = load_settings(env_file=env_file)

    assert isinstance(settings, Settings)
    assert settings.adapta_login == "user@example.com"
    assert settings.adapta_password == "secret"
    assert settings.adapta_model == "gpt"
    assert settings.env_file_path == env_file


def test_load_settings_requires_credentials(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text('ADAPTA_LOGIN="user@example.com"\n', encoding="utf-8")

    with pytest.raises(ValueError):
        load_settings(env_file=env_file)
