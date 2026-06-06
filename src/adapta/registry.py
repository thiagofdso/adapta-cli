from __future__ import annotations

from adapta.models import ModelOption


MODEL_OPTIONS: tuple[ModelOption, ...] = (
    ModelOption(
        "one",
        "ONE",
        "ONE",
        summary=(
            "Exclusivo da Adapta; escolhe automaticamente a melhor IA por prompt "
            "em um único chat."
        ),
    ),
    ModelOption(
        "onepro",
        "ONE Pro",
        "ONE_PRO",
        summary=(
            "Passa o prompt por 3 IAs para respostas mais completas e com menor risco"
            " de lacunas."
        ),
    ),
    ModelOption(
        "onesuperfast",
        "ONE Superfast",
        "ONE_SUPERFAST",
        summary=(
            "Versão ultra-rápida do ONE usando Claude 4.5 Haiku para respostas ágeis "
            "sem perder inteligência automática."
        ),
    ),
    ModelOption(
        "gpt54",
        "GPT-5.4",
        "GPT_54",
        summary=(
            "Modelo GPT-5 mais avançado com 1,1M tokens de contexto e raciocínio de ponta."
        ),
    ),
    ModelOption(
        "gpt51",
        "GPT-5.1",
        "GPT_51",
        summary=(
            "Versão otimizada para velocidade do GPT-5, mantendo alta qualidade com latência baixa."
        ),
    ),
    ModelOption(
        "gemini31",
        "Gemini 3.1 Pro Preview",
        "GEMINI_3_1_PRO_PREVIEW",
        summary=(
            "Modelo Google com raciocínio 2x superior ao Gemini 3 Pro, suporte a 1M tokens e ótimo para código."
        ),
    ),
    ModelOption(
        "geminiflash",
        "Gemini 3 Flash",
        "GEMINI_3_FLASH",
        summary=(
            "Versão mais rápida do Gemini 3, com contexto expandido e respostas instantâneas."
        ),
    ),
    ModelOption(
        "claude46",
        "Claude 4.6 Sonnet",
        "CLAUDE_4_6_SONNET",
        summary=(
            "Modelo híbrido da Anthropic que equilibra raciocínio profundo e velocidade para programação."
        ),
    ),
    ModelOption(
        "claude45h",
        "Claude 4.5 Haiku",
        "CLAUDE_4_5_HAIKU",
        summary=(
            "Modelo mais rápido da Anthropic, ideal para análise veloz de grandes documentos."
        ),
    ),
    ModelOption(
        "deepseekreasoner",
        "DeepSeek V3.2 Reasoner",
        "DEEPSEEK_V3_2_REASONER",
        summary=(
            "Reasoning explícito durante o streaming; excelente para problemas passo a passo."
        ),
    ),
    ModelOption(
        "deepseek",
        "DeepSeek V3.2",
        "DEEPSEEK_V3_2",
        summary=(
            "Versão avançada da DeepSeek com ótimo custo-benefício em código e matemática."
        ),
    ),
    ModelOption(
        "grok",
        "Grok 4.1",
        "GROK_41",
        summary=(
            "Respostas rápidas com raciocínio explícito; ideal para problemas complexos com explicações detalhadas."
        ),
    ),
    ModelOption(
        "kimi",
        "Kimi K2.5",
        "KIMI_K2_5",
        summary="Modelo da Moonshot com foco em código e raciocínio.",
    ),
    ModelOption(
        "minimax",
        "MiniMax M2.7",
        "MINIMAX_M2_7",
        summary=(
            "SOTA em coding (80.2% SWE-Bench), 1M tokens de contexto e ótima produtividade."
        ),
    ),
    ModelOption(
        "glm5",
        "GLM-5",
        "GLM_5",
        summary=(
            "Modelo da Zhipu AI com 203K tokens de contexto e grande capacidade de geração."
        ),
    ),
    ModelOption(
        "llama4",
        "Llama 4 Maverick",
        "LLAMA_4_MAVERICK",
        summary=(
            "Novo modelo da Meta com performance equivalente ao GPT-4o/Claude 3.5 Sonnet."
        ),
    ),
    ModelOption(
        "sonar",
        "Sonar Pro",
        "SONAR_PRO",
        summary="IA otimizada para busca em tempo real na internet.",
    ),
    ModelOption(
        "qwen35",
        "Qwen 3.5 Plus",
        "QWEN_3_5_PLUS",
        summary=(
            "Modelo multilíngue da Alibaba, excelente em 29+ idiomas e análise de dados estruturados."
        ),
    ),
)

ALIASES = {
    "gpt": "gpt54",
    "gpt-5": "gpt54",
    "gpt_5": "gpt54",
    "gpt-5.4": "gpt54",
    "gpt_5_4": "gpt54",
    "gpt-5.1": "gpt51",
    "gpt_51": "gpt51",
    "one-pro": "onepro",
    "one_pro": "onepro",
    "one-superfast": "onesuperfast",
    "one_superfast": "onesuperfast",
    "gemini": "gemini31",
    "gemini-pro": "gemini31",
    "gemini-flash": "geminiflash",
    "claude": "claude46",
    "claude-sonnet": "claude46",
    "claude-haiku": "claude45h",
    "deepseek-v3": "deepseek",
    "deepseek-v3.2": "deepseek",
    "deepseek-reasoner": "deepseekreasoner",
    "qwen": "qwen35",
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
