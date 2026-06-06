# CLI Contract: `adapta pipeline`

## Command

```text
adapta pipeline --input-dir PATH --output-dir PATH [--db-path PATH] [--mode upload|docling] [--job INTEGER] [--keep-chat] [--log]
```

## Inputs

### Options

- `--input-dir PATH`
  - diretório raiz com arquivos compatíveis para processamento em lote
  - obrigatório
- `--output-dir PATH`
  - diretório onde os artefatos do pipeline devem ser gravados
  - obrigatório
- `--db-path PATH`
  - caminho explícito do banco SQLite local usado pela execução
  - opcional
  - tem precedência sobre a variável de ambiente
- `--mode upload|docling`
  - seleciona o modo operacional compatível com o pipeline legado
  - opcional
  - padrão: `upload`
- `--job INTEGER`
  - restringe a execução a um job já registrado no banco quando aplicável
  - opcional
- `--keep-chat`
  - preserva o chat operacional criado durante chamadas ao modelo quando aplicável
  - opcional
- `--log`
  - habilita emissão de progresso operacional no terminal
  - opcional

### Environment

- `ADAPTA_PIPELINE_DB_PATH`
  - caminho alternativo para o banco SQLite do pipeline
  - usado apenas quando `--db-path` não for informado

## Resolution Order

1. Usar `--db-path` quando presente.
2. Senão, usar `ADAPTA_PIPELINE_DB_PATH` quando presente.
3. Senão, usar o caminho padrão documentado `~/.local/state/adapta-cli/pipeline.db`.

## Processing Contract

- o comando deve varrer `--input-dir` recursivamente
- o comando deve considerar apenas tipos de arquivo compatíveis com o pipeline original
- o comando deve preservar o formato funcional de entrada e saída já esperado do pipeline legado
- o comando deve usar SQLite local para registrar o estado operacional da execução
- o comando deve gravar índices, artefatos documentais e demais saídas apenas dentro de `--output-dir`, exceto pelo banco quando ele usar o caminho padrão ou um caminho customizado fora do diretório de saída
- o comando não pode depender de importação de código-fonte externo em runtime

## Output Contract

### Success

- gravar os artefatos produzidos pela execução em `--output-dir`
- informar no terminal um resumo orientado a status e os destinos produzidos

### Failure

- emitir erro em stderr com mensagem curta e acionável
- encerrar com código `1`
- falhas esperadas não devem exibir traceback verboso

## Validation Rules

- `--input-dir` deve existir e ser legível
- `--output-dir` deve ser utilizável para gravação
- `--db-path`, quando informado ou resolvido por ambiente, deve ser gravável ou criável
- `--mode` deve aceitar apenas valores suportados
- diretório sem arquivos compatíveis deve falhar cedo com mensagem clara
- erros de permissão no banco devem falhar cedo com mensagem clara

## Operational Guarantees

- a precedência entre parâmetro, ambiente e padrão para o banco deve ser determinística
- o comando deve permanecer compatível com o comportamento funcional do pipeline original para formatos e artefatos suportados
- falhas de cleanup best-effort não devem invalidar artefatos já produzidos com sucesso
