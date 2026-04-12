# CLI Contract: `adapta debate`

## Command

```text
adapta debate [--config PATH] [--rounds INTEGER] [--output PATH] --prompt TEXT [--model-conclusion MODEL_KEY]
```

## Inputs

### Options

- `--config PATH`
  - caminho para arquivo JSON com a definição dos agentes
  - tem precedência sobre `ADAPTA_DEBATE_CONFIG`
- `--rounds INTEGER`
  - número de rodadas do debate
  - quando ausente, deve ser solicitado interativamente
- `--output PATH`
  - caminho opcional para salvar o resultado completo do debate
- `--prompt TEXT`
  - tema ou problema principal do debate
- `--model-conclusion MODEL_KEY`
  - modelo responsável pela conclusão final
  - padrão: `gemini`

### Environment

- `ADAPTA_DEBATE_CONFIG`
  - caminho alternativo para arquivo JSON de configuração de agentes
  - usado apenas quando `--config` não for informado

## Configuration File Contract

O arquivo de configuração deve ser um objeto JSON cujas chaves identificam os agentes.

```json
{
  "A1": {
    "model": "claude",
    "prompt": "voce e um arquiteto de ti"
  },
  "A2": {
    "model": "claude",
    "prompt": "voce e um desenvolvedor"
  }
}
```

## Resolution Order

1. Usar `--config` quando presente.
2. Senão, usar `ADAPTA_DEBATE_CONFIG` quando presente e válido.
3. Senão, iniciar fluxo interativo e salvar `debate.json` no diretório corrente.

## Interactive Contract

Quando a configuração não vier por arquivo nem ambiente, o comando deve perguntar nesta ordem:

1. quantidade de agentes
2. modelo do agente 1
3. prompt do agente 1
4. repetir modelo e prompt para cada agente seguinte
5. número de rodadas, quando `--rounds` estiver ausente

Regras:

- quantidade de agentes deve ser numérica e maior ou igual a 2
- número de rodadas deve ser numérico e maior que 0
- respostas inválidas devem gerar mensagem curta e nova solicitação ou encerramento controlado

## Output Contract

### Without `--output`

- imprimir cada resposta assim que a rodada do agente terminar
- identificar cada bloco com cabeçalho equivalente a `Agente 1 Rodada 1`
- imprimir a conclusão final ao término do debate

### With `--output`

- salvar o artefato completo do debate no caminho informado
- manter mensagens de terminal mínimas e orientadas a status

## Errors

Erros esperados devem:

- ser emitidos em stderr
- usar mensagem curta e acionável
- encerrar com código `1`
- evitar traceback em condições operacionais esperadas
