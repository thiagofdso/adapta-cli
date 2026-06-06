from __future__ import annotations

import asyncio
import os
import time
import uuid
from typing import Any

import pytest

from adapta.client import create_client
from adapta.config import load_settings
from adapta.registry import get_model_option


RUN_REAL_TESTS = os.getenv("ADAPTA_RUN_PARALLEL_GPT_TESTS") == "1"
MEDIUM_COMPLEXITY_PROMPT = """
Você é um analista de operações SaaS B2B.

Cenário:
- uma startup vende software para equipes comerciais
- a conversão de trial para pago caiu de 18% para 11% nos últimos 60 dias
- o CAC subiu 22% no mesmo período
- o onboarding foi encurtado de 14 para 5 dias
- o time de suporte relata aumento de dúvidas sobre integrações

Tarefa:
- identifique as 3 hipóteses mais prováveis para a queda de conversão
- proponha um plano de investigação para os próximos 14 dias
- descreva 2 riscos de execução

Restrições:
- responda em português
- seja objetivo
- use os títulos Hipóteses, Plano e Riscos
- limite total aproximado de 220 palavras
""".strip()


def _read_positive_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    value = int(raw_value)
    if value < 1:
        raise ValueError(f"{name} deve ser maior que zero.")
    return value


async def _run_parallel_batch(
    *,
    client: Any,
    model_backend: str,
    batch_size: int,
    created_chat_ids: list[str],
) -> dict[str, Any]:
    started_at = time.perf_counter()
    chat_ids = [str(uuid.uuid4()) for _ in range(batch_size)]
    created_chat_ids.extend(chat_ids)
    tasks = [
        client.chat(
            model_backend=model_backend,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{MEDIUM_COMPLEXITY_PROMPT}\n\n"
                        f"Contexto de execução: lote={batch_size}, chamada={index}."
                    ),
                }
            ],
            chat_id=chat_ids[index - 1],
        )
        for index in range(1, batch_size + 1)
    ]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)
    elapsed_seconds = time.perf_counter() - started_at

    success_count = 0
    failure_messages: list[str] = []
    for result in raw_results:
        if isinstance(result, Exception):
            failure_messages.append(f"{type(result).__name__}: {result}")
            continue
        if not str(result).strip():
            failure_messages.append("RuntimeError: resposta vazia")
            continue
        success_count += 1

    return {
        "batch_size": batch_size,
        "success_count": success_count,
        "failure_count": len(failure_messages),
        "elapsed_seconds": elapsed_seconds,
        "first_failure": failure_messages[0] if failure_messages else None,
    }


@pytest.mark.skipif(
    not RUN_REAL_TESTS,
    reason="Teste real de paralelismo GPT desabilitado; defina ADAPTA_RUN_PARALLEL_GPT_TESTS=1",
)
@pytest.mark.anyio
async def test_gpt_parallel_progressive_limit() -> None:
    if not (os.getenv("ADAPTA_LOGIN") and os.getenv("ADAPTA_PASSWORD")):
        pytest.skip("Credenciais ADAPTA_LOGIN e ADAPTA_PASSWORD não disponíveis")

    start_parallel = _read_positive_int("ADAPTA_PARALLEL_GPT_START", 3)
    step_parallel = _read_positive_int("ADAPTA_PARALLEL_GPT_STEP", 3)
    max_parallel = _read_positive_int("ADAPTA_PARALLEL_GPT_MAX", 30)
    if max_parallel < start_parallel:
        raise ValueError("ADAPTA_PARALLEL_GPT_MAX deve ser maior ou igual ao início.")

    settings = load_settings()
    model_backend = get_model_option("gpt").backend_name
    batches: list[dict[str, Any]] = []
    created_chat_ids: list[str] = []

    async with create_client(settings) as client:
        try:
            for batch_size in range(start_parallel, max_parallel + 1, step_parallel):
                batch_result = await _run_parallel_batch(
                    client=client,
                    model_backend=model_backend,
                    batch_size=batch_size,
                    created_chat_ids=created_chat_ids,
                )
                batches.append(batch_result)
                print(
                    "lote=%s sucesso=%s falha=%s duracao=%.2fs"
                    % (
                        batch_result["batch_size"],
                        batch_result["success_count"],
                        batch_result["failure_count"],
                        batch_result["elapsed_seconds"],
                    )
                )
                if batch_result["first_failure"] is not None:
                    print(f"primeira_falha={batch_result['first_failure']}")
                    break
        finally:
            if created_chat_ids:
                await client.delete_chat(created_chat_ids)
                print(f"chats_removidos={len(created_chat_ids)}")

    assert batches, "Nenhum lote foi executado."
    assert batches[0]["failure_count"] == 0, (
        "O lote inicial falhou; revise credenciais, disponibilidade do serviço "
        "ou reduza a concorrência inicial."
    )

    highest_successful_batch = max(
        batch["batch_size"] for batch in batches if batch["failure_count"] == 0
    )
    print(f"maior_lote_sem_falha={highest_successful_batch}")
