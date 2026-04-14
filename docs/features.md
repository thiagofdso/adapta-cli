# Features

## Prompt único por terminal

Status: ativo

Descrição: envia um prompt inline ou por arquivo e retorna a resposta no terminal, com opção de salvar em arquivo. Também aceita `--file` com 1 a 5 anexos separados por vírgula, fazendo upload antes de chamar o modelo.

Depende de: autenticação Adapta, registro de modelos, cliente de prompt.

## Chat interativo

Status: ativo

Descrição: inicia uma conversa contextual com o modelo e exclui o chat remoto ao encerrar. Também aceita `--file` com 1 a 5 anexos separados por vírgula, reaproveitando os mesmos anexos em cada mensagem da sessão.

Depende de: autenticação Adapta, registro de modelos, cliente de chat.

## Gerador de persona

Status: ativo

Descrição: expõe o comando `persona` para conduzir uma entrevista interativa em 6 blocos, gerar um markdown de persona com `--model` opcional e salvar o resultado na pasta de personas sob o diretório home do usuário, em um caminho equivalente a `~/.adapta/persona/{nome-persona}.md`. O comando valida nome e cargo, aceita campos opcionais vazios, salva também um JSON com todas as respostas, aceita `--input-file` para gerar a persona a partir de um JSON preenchido e aceita `--update` para reler o JSON salvo, permitir ajustes interativos e regerar o prompt. O fluxo continua pedindo confirmação imediata se os arquivos já existirem e tenta excluir o chat remoto ao final.

Depende de: autenticação Adapta, registro de modelos, cliente de chat, persistência local de saída e resolução multiplataforma do diretório home.

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

Descrição: expõe o comando `debate` para executar múltiplos agentes por rodadas, com configuração por arquivo JSON, variável de ambiente ou fluxo interativo, conclusão final consolidada e saída no terminal ou em arquivo. No JSON de configuração, cada agente pode definir opcionalmente `persona` apontando para um arquivo de persona cujo conteúdo é incorporado ao prompt do agente. Também aceita `--file` com 1 a 5 anexos separados por vírgula, faz upload único no início da execução e reutiliza esses arquivos em todas as mensagens dos agentes. Com `--control`, o usuário pode intervir a cada resposta para continuar o fluxo atual, responder um agente, responder todos, fazer um agente responder a outro, fazer um agente responder a todos ou encerrar imediatamente com conclusão final.

Depende de: autenticação Adapta, registro de modelos, cliente de chat, persistência local de saída e validação interativa de entrada.

## Pipeline por diretório

Status: ativo

Descrição: expõe o comando `pipeline` para processar lotes em `--input-dir` e gravar artefatos compatíveis com o pipeline legado em `--output-dir`, preservando o formato funcional de entrada e saída. O comando usa SQLite local para estado operacional, com caminho padrão em `~/.local/state/adapta-cli/pipeline.db`, customização por `ADAPTA_PIPELINE_DB_PATH` e precedência do parâmetro `--db-path` quando informado. Arquivos `.txt` são enviados inline no prompt, sem upload remoto.

Depende de: autenticação Adapta, upload de arquivo, prompts internalizados de extração e criação de conhecimento, persistência local em SQLite e escrita de artefatos em filesystem.

## Importação de cookies de sessão

Status: ativo

Descrição: expõe o comando `import-cookies` para converter um arquivo de export de cookies do navegador, como `session.json`, para o cache local `~/.adapta/cookies.json`. O comando extrai cookies, infere `session_id` do contexto Clerk e atualiza o backup de sessão usado pela CLI para evitar novo login nas chamadas seguintes.

Depende de: filesystem local e formato JSON compatível de export de cookies.

## Destilador por arquivo ou diretório

Status: ativo

Descrição: expõe o comando `destilador` para processar um PDF ou `.txt` único com `--input` e `--output`, um item único com `--input` e `--output-dir`, ou um lote com `--input-dir` e `--output-dir`, internalizando no próprio CLI a lógica de destilação em 7 dimensões para gerar um markdown consolidado por item. Antes do upload, o cliente consulta a listagem remota de arquivos e reaproveita o artefato existente quando o mesmo nome já está presente. Quando o arquivo é `.txt`, o conteúdo é incluído diretamente no prompt e nenhum upload remoto é feito. No modo `--input` com `--output-dir`, o comando também preserva os arquivos parciais por dimensão.

Depende de: autenticação Adapta, upload de arquivo, prompts de destilação internalizados em `src/adapta/prompts/livro/`, persistência local de saída e limpeza best-effort de artefatos temporários e remotos.

## Instalação e atalhos locais

Status: ativo

Descrição: disponibiliza scripts de instalação e atalhos via `Makefile` para testes, prompt, chat, instalação local e remota, priorizando `pipx` quando disponível e com fallback para `venv` dedicada com link em `~/.local/bin/adapta`.

Depende de: empacotamento Python e scripts de shell.
