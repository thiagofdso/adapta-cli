import pytest

from adapta.logging import resolve_log_level


def test_resolve_log_level_returns_none_by_default() -> None:
    assert resolve_log_level(None) is None


def test_resolve_log_level_accepts_info_and_debug() -> None:
    assert resolve_log_level("info") == "INFO"
    assert resolve_log_level("debug") == "DEBUG"


def test_resolve_log_level_rejects_unknown_level() -> None:
    with pytest.raises(ValueError):
        resolve_log_level("warn")
