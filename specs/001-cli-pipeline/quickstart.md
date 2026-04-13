# Quickstart: Comando pipeline por diretório

## Pré-requisitos

- configurar `ADAPTA_LOGIN` e `ADAPTA_PASSWORD`
- ter um diretório de entrada com arquivos compatíveis com o pipeline original
- ter permissão de escrita para `--output-dir`
- ter permissão de escrita para o banco SQLite resolvido

## Execução mínima

```text
adapta pipeline --input-dir ./entrada --output-dir ./saida
```

Comportamento esperado:

- usa o banco padrão em `~/.local/state/adapta-cli/pipeline.db`
- varre `./entrada` recursivamente
- grava os artefatos gerados em `./saida`

## Customizar banco por ambiente

```text
ADAPTA_PIPELINE_DB_PATH=/tmp/pipeline.db adapta pipeline --input-dir ./entrada --output-dir ./saida
```

## Customizar banco por parâmetro explícito

```text
adapta pipeline --input-dir ./entrada --output-dir ./saida --db-path /tmp/pipeline.db
```

## Executar com flags operacionais compatíveis

```text
adapta pipeline --input-dir ./entrada --output-dir ./saida --mode upload --keep-chat --log
```

## Verificações recomendadas

- confirmar que os artefatos foram gravados somente em `--output-dir`
- confirmar que o banco foi criado no caminho esperado segundo a precedência configurada
- validar mensagens curtas para diretório inexistente, lote vazio e falha de permissão no banco
