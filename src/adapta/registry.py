from __future__ import annotations

from adapta.models import ModelOption


MODEL_OPTIONS: tuple[ModelOption, ...] = (
    ModelOption("claude", "Claude 4.5 Sonnet", "CLAUDE_4_5_SONNET"),
    ModelOption("gemini", "Gemini 3 Pro Preview", "GEMINI_3_PRO_PREVIEW"),
    ModelOption("grok", "Grok 4.1", "GROK_41"),
    ModelOption("gpt", "GPT-5", "GPT_5"),
    ModelOption("gpt51", "GPT-5.1", "GPT_51"),
    ModelOption("deepseek", "Deepseek V3", "DEEPSEEK_V3"),
    ModelOption("qwen", "Qwen3 Max", "QWEN3_MAX"),
    ModelOption("one", "One Pro", "ONE_PRO"),
    ModelOption("o3", "O3", "O3"),
    ModelOption("sonar", "Sonar Pro", "SONAR_PRO"),
)

ALIASES = {
    "gpt-5": "gpt",
    "gpt_5": "gpt",
    "gpt-5.1": "gpt51",
    "gpt_51": "gpt51",
    "one-pro": "one",
    "sonar-pro": "sonar",
}


def list_model_options() -> list[ModelOption]:
    return list(MODEL_OPTIONS)


def get_model_option(key: str) -> ModelOption:
    normalized = key.strip().lower()
    normalized = ALIASES.get(normalized, normalized)

    for option in MODEL_OPTIONS:
        if option.key == normalized:
            return option
    raise ValueError(f"Modelo inválido: {key}")


def resolve_model_key(explicit: str | None, default: str | None) -> str:
    candidate = explicit or default
    if not candidate:
        raise ValueError("Nenhum modelo informado.")
    return get_model_option(candidate).key
