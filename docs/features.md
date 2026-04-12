# Features

## Prompt único por terminal

Status: ativo

Descrição: envia um prompt inline ou por arquivo e retorna a resposta no terminal, com opção de salvar em arquivo.

Depende de: autenticação Adapta, registro de modelos, cliente de prompt.

## Chat interativo

Status: ativo

Descrição: inicia uma conversa contextual com o modelo e exclui o chat remoto ao encerrar.

Depende de: autenticação Adapta, registro de modelos, cliente de chat.

## Seleção de modelo

Status: ativo

Descrição: usa `--model`, `ADAPTA_MODEL` ou seleção interativa quando necessário.

Depende de: configuração de ambiente e registro de modelos.

## Listagem de modelos

Status: ativo

Descrição: expõe o comando `models` para listar no terminal todas as opções disponíveis com chave, nome amigável e identificador do backend.

Depende de: registro de modelos.

## Instalação e atalhos locais

Status: ativo

Descrição: disponibiliza scripts de instalação e atalhos via `Makefile` para testes, prompt, chat, instalação local e remota, priorizando `pipx` quando disponível e com fallback para `venv` dedicada com link em `~/.local/bin/adapta`.

Depende de: empacotamento Python e scripts de shell.
