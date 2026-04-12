# Features

## Prompt único por terminal

Status: ativo

Descrição: envia um prompt inline ou por arquivo e retorna a resposta no terminal, com opção de salvar em arquivo. Também aceita `--file` com 1 a 5 anexos separados por vírgula, fazendo upload antes de chamar o modelo.

Depende de: autenticação Adapta, registro de modelos, cliente de prompt.

## Chat interativo

Status: ativo

Descrição: inicia uma conversa contextual com o modelo e exclui o chat remoto ao encerrar. Também aceita `--file` com 1 a 5 anexos separados por vírgula, reaproveitando os mesmos anexos em cada mensagem da sessão.

Depende de: autenticação Adapta, registro de modelos, cliente de chat.

## Seleção de modelo

Status: ativo

Descrição: usa `--model`, `ADAPTA_MODEL` ou seleção interativa quando necessário.

Depende de: configuração de ambiente e registro de modelos.

## Listagem de modelos

Status: ativo

Descrição: expõe o comando `models` para listar no terminal todas as opções disponíveis com chave, nome amigável e identificador do backend.

Depende de: registro de modelos.

## Listagem de arquivos remotos

Status: ativo

Descrição: expõe o comando `list-files` para listar no terminal os arquivos remotos já disponíveis na conta, exibindo nome, caminho, tipo de mídia e tamanho.

Depende de: autenticação Adapta e cliente de listagem de arquivos.

## Debate multiagente

Status: planejado

Descrição: expõe o comando `debate` para executar múltiplos agentes por rodadas, com configuração por arquivo JSON, variável de ambiente ou fluxo interativo, conclusão final consolidada e saída no terminal ou em arquivo. Também aceita `--file` com 1 a 5 anexos separados por vírgula, faz upload único no início da execução e reutiliza esses arquivos em todas as mensagens dos agentes.

Depende de: autenticação Adapta, registro de modelos, cliente de chat, persistência local de saída e validação interativa de entrada.

## Destilador por arquivo ou diretório

Status: ativo

Descrição: expõe o comando `destilador` para processar um PDF único com `--input` e `--output`, um PDF único com `--input` e `--output-dir`, ou um lote com `--input-dir` e `--output-dir`, internalizando no próprio CLI a lógica de destilação em 7 dimensões para gerar um markdown consolidado por item. Antes do upload, o cliente consulta a listagem remota de arquivos e reaproveita o artefato existente quando o mesmo nome já está presente. No modo `--input` com `--output-dir`, o comando também preserva os arquivos parciais por dimensão.

Depende de: autenticação Adapta, upload de arquivo, prompts de destilação internalizados em `src/adapta/prompts/livro/`, persistência local de saída e limpeza best-effort de artefatos temporários e remotos.

## Instalação e atalhos locais

Status: ativo

Descrição: disponibiliza scripts de instalação e atalhos via `Makefile` para testes, prompt, chat, instalação local e remota, priorizando `pipx` quando disponível e com fallback para `venv` dedicada com link em `~/.local/bin/adapta`.

Depende de: empacotamento Python e scripts de shell.
