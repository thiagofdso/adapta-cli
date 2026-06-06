# CLI Contract: `adapta destilador`

## Command

```text
adapta destilador (--input PATH (--output PATH | --output-dir PATH) | --input-dir PATH --output-dir PATH)
```

## Inputs

### Options

- `--input PATH`
  - arquivo individual a ser processado pelo pipeline de destilação
  - obrigatório
- `--output PATH`
  - caminho do arquivo consolidado final
  - obrigatório
- `--input-dir PATH`
  - diretório com múltiplos arquivos compatíveis para processamento em lote
  - obrigatório no modo por diretório
- `--output-dir PATH`
  - diretório onde será gravado um consolidado por item processado
  - obrigatório no modo por diretório e opcional no modo por arquivo quando o usuário quiser preservar parciais e gravar o consolidado em um diretório

## Processing Contract

- o comando deve internalizar no próprio projeto a lógica necessária do pipeline de destilação
- antes do upload, o cliente deve consultar a listagem remota de arquivos para evitar reenvio redundante quando já existir arquivo com o mesmo nome
- o comando deve gerar dimensões intermediárias antes de produzir o consolidado final
- o comando deve tratar retries operacionais de dimensões sem expor detalhes internos desnecessários ao usuário
- no modo por diretório, o comando deve processar cada item compatível encontrado e gerar um arquivo final correspondente
- no modo `--input` + `--output-dir`, o comando deve gravar o consolidado do arquivo em um diretório explícito e preservar os artefatos parciais por dimensão

## Output Contract

### Success

- gravar o consolidado final exatamente em `--output`
- informar no terminal que o arquivo final foi salvo

### Success with `--input-dir` + `--output-dir`

- gravar um consolidado final por item processado em `--output-dir`
- informar no terminal o resumo dos itens processados e seus destinos

### Success with `--input` + `--output-dir`

- gravar o consolidado final do arquivo individual em `--output-dir`
- preservar os arquivos parciais de dimensões em um subdiretório derivado do nome do arquivo

### Failure

- emitir erro em stderr com mensagem curta e acionável
- encerrar com código `1`
- preservar artefatos intermediários quando a falha justificar análise posterior

## Validation Rules

- `--input` deve existir e ser legível
- `--output` deve ser gravável ou sobrescrevível
- `--input-dir` deve existir e ser legível
- `--output-dir` deve ser utilizável para gravação
- entradas incompatíveis devem ser rejeitadas antes do processamento remoto
- `--input-dir` com `--output` deve ser rejeitado

## Operational Guarantees

- a listagem remota de arquivos deve ser paginada e reutilizável por outros comandos do CLI, inclusive `list-files`
- limpeza de uploads temporários e artefatos remotos deve ser best-effort
- falha de limpeza não deve invalidar uma execução que já produziu o consolidado final
- a funcionalidade não pode depender de apontamento para código-fonte externo em runtime
