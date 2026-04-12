# CLI Contract: Build Adapta CLI

## Command Group

- Executable name: `adapta`
- Global options:
- `--log TEXT`
- Primary subcommands:
- `adapta prompt`
- `adapta chat`

## Installation Contract

- Scripts esperados:
- `scripts/install-local.sh`
- `scripts/install-remote.sh`

## Make Contract

- Arquivo esperado:
- `Makefile`

### Required Targets

- `make test`
- `make prompt`
- `make chat`

### `make test`

- Purpose: Executa a suíte de testes do projeto.

### `make prompt`

- Purpose: Executa o fluxo de prompt da CLI com parâmetros padronizados ou variáveis recebidas via `make`.

### `make chat`

- Purpose: Inicia o fluxo de chat da CLI com parâmetros padronizados ou variáveis recebidas via `make`.

### Rules

- Os alvos `prompt` e `chat` devem encaminhar para o comando oficial `adapta`.
- Os alvos devem permitir parametrização por variáveis de ambiente ou variáveis passadas na chamada do `make`.
- O `Makefile` não deve duplicar a lógica de negócio da CLI; deve apenas facilitar a invocação.

### `scripts/install-local.sh`

- Purpose: Instala o projeto atual e disponibiliza `adapta` no sistema usando os arquivos locais.
- Inputs:
- caminho opcional do projeto local; quando omitido, usa a raiz atual
- Success Behavior:
- conclui sem erro
- `adapta --help` fica disponível no ambiente alvo
- Failure Behavior:
- encerra com erro claro se o ambiente de Python necessário não estiver disponível

### `scripts/install-remote.sh`

- Purpose: Instala a CLI a partir de um repositório remoto informado pela pessoa usuária.
- Inputs:
- URL do repositório remoto
- referência opcional de branch, tag ou commit
- Success Behavior:
- conclui sem erro
- `adapta --help` fica disponível no ambiente alvo
- Failure Behavior:
- encerra com erro claro se o repositório não puder ser acessado ou instalado

## Global Logging Rules

- A CLI não deve emitir logs operacionais quando `--log` não for informado.
- `--log` deve permitir escolher o nível de log da execução.
- Os níveis mínimos suportados devem incluir `info` e `debug`.
- A resposta principal do comando não é considerada log e deve continuar visível.

## `adapta prompt`

### Purpose

- Executa um prompt único e retorna a resposta imediatamente.

### Inputs

- `--model TEXT`: opcional; chave curta do modelo
- `--prompt TEXT`: opcional; prompt inline
- `--prompt-file PATH`: opcional; arquivo com o prompt
- `--output PATH`: opcional; arquivo para salvar a resposta

### Rules

- Deve aceitar exatamente uma das opções `--prompt` ou `--prompt-file`.
- Quando `--model` não for informado, deve usar `ADAPTA_MODEL`.
- Quando `--model` não for informado e `ADAPTA_MODEL` não existir, deve apresentar seleção interativa de modelo antes de continuar.
- Quando `--output` for informado, deve gravar a mesma resposta textual retornada no terminal.

### Success Behavior

- Exit code `0`
- Resposta escrita em `stdout`
- Arquivo de saída gravado quando solicitado

### Failure Behavior

- Exit code diferente de `0` para parâmetros inválidos, erro de leitura, erro de autenticação, modelo inexistente ou falha de escrita
- Mensagem de erro objetiva em `stderr`

## `adapta chat`

### Purpose

- Inicia uma sessão conversacional interativa com contexto acumulado.

### Inputs

- `--model TEXT`: opcional; chave curta do modelo

### Rules

- Quando `--model` não for informado, deve usar `ADAPTA_MODEL`.
- Quando `--model` não for informado e `ADAPTA_MODEL` não existir, deve apresentar seleção interativa de modelo antes de iniciar a sessão.
- Deve manter o histórico da sessão localmente durante a execução.
- Deve tentar excluir o chat remoto ao final da sessão.

### Success Behavior

- Exit code `0`
- Cada mensagem do usuário gera uma resposta contextualizada
- Encerramento limpa a sessão remota criada pela CLI

### Failure Behavior

- Exit code diferente de `0` para autenticação inválida, erro fatal de comunicação ou seleção inválida de modelo
- Se a limpeza do chat falhar, a CLI deve avisar em `stderr` antes de sair

## Integration Assertions

- `adapta prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"` deve permitir validar uma resposta igual a `2`.
- `adapta prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"` deve permitir validar saída sem linhas extras de log.
- `adapta --log info prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"` deve permitir validar log mínimo.
- `adapta --log debug prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"` deve permitir validar log detalhado.
- `adapta prompt --model gpt --prompt-file prompt.txt --output resposta.txt` deve escrever a resposta em `stdout` e em `resposta.txt`.
- `adapta chat --model gpt` deve criar uma sessão temporária e solicitar sua exclusão ao final.
- `scripts/install-local.sh` deve tornar `adapta` executável a partir da origem local.
- `scripts/install-remote.sh <repo>` deve tornar `adapta` executável a partir da origem remota informada.
- `make test` deve executar a suíte do projeto.
- `make prompt` deve executar o fluxo de prompt.
- `make chat` deve iniciar o fluxo de chat.
