# Quickstart: Debate no CLI

## Pré-requisitos

- Variáveis `ADAPTA_LOGIN` e `ADAPTA_PASSWORD` configuradas.
- Ambiente local capaz de executar `python -m adapta.cli` ou o binário instalado `adapta`.

## Executar com arquivo de configuração

1. Criar um arquivo `debate.json`:

```json
{
  "A1": {
    "model": "claude",
    "prompt": "voce e um arquiteto de ti"
  },
  "A2": {
    "model": "gpt",
    "prompt": "voce e um desenvolvedor senior"
  }
}
```

2. Rodar o comando:

```bash
python -m adapta.cli debate --config debate.json --rounds 3 --prompt "Defina a arquitetura de um novo portal interno" --model-conclusion gemini
```

## Executar usando variável de ambiente

```bash
export ADAPTA_DEBATE_CONFIG="$PWD/debate.json"
python -m adapta.cli debate --rounds 2 --prompt "Compare duas estratégias de rollout"
```

## Executar em modo interativo

```bash
python -m adapta.cli debate --prompt "Como reduzir o tempo de onboarding técnico?"
```

Fluxo esperado:

1. informar número de agentes
2. escolher o modelo e o prompt de cada agente
3. informar o número de rodadas, se ausente
4. confirmar início do debate
5. reaproveitar `debate.json` salvo automaticamente em execuções futuras

## Salvar em arquivo

```bash
python -m adapta.cli debate --config debate.json --rounds 3 --prompt "Planeje uma migração" --output debate.md
```

## Validação esperada

- configurações com menos de 2 agentes devem falhar
- entradas não numéricas para agentes ou rodadas devem ser rejeitadas
- caminho inválido em `--config` ou `ADAPTA_DEBATE_CONFIG` deve falhar com mensagem curta
- falhas de cleanup remoto devem aparecer como aviso, sem invalidar um debate já concluído
