import pytest

from adapta.registry import get_model_option, list_model_options, resolve_model_key


def test_get_model_option_supports_known_alias() -> None:
    option = get_model_option("gpt")

    assert option.key == "gpt54"
    assert option.backend_name == "GPT_54"


def test_list_model_options_returns_options() -> None:
    options = list_model_options()

    assert options
    assert all(option.display_name for option in options)


def test_resolve_model_key_prefers_explicit_value() -> None:
    assert resolve_model_key(explicit="claude46", default="gpt") == "claude46"


def test_resolve_model_key_uses_default_when_explicit_missing() -> None:
    assert resolve_model_key(explicit=None, default="gpt") == "gpt54"


def test_resolve_model_key_raises_when_missing() -> None:
    with pytest.raises(ValueError):
        resolve_model_key(explicit=None, default=None)
