# Code Map

## Estrutura

- `src/adapta/cli.py` -> comandos Typer, parsing da linha de comando, parsing de anexos `--file`, listagem de modelos, listagem de arquivos remotos, importação de cookies, fluxo interativo do debate, entrevista do comando `persona` e entrada explícita de `destilador` e `pipeline`
- `src/adapta/config.py` -> carregamento de `.env`, configurações tipadas e resolução do caminho do banco do pipeline
- `src/adapta/logging.py` -> configuração de logs por execução
- `src/adapta/registry.py` -> catálogo de modelos e resolução de aliases
- `src/adapta/runtime.py` -> ponte síncrona para fluxos assíncronos
- `src/adapta/client.py` -> cliente interno do Adapta com classes focadas em sessão HTTP, autenticação, cache local de sessão em `~/.adapta/cookies.json`, importação de export de cookies do navegador, listagem/upload/exclusão de arquivos e conversas com SSE
- `src/adapta/services/prompt_service.py` -> fluxo de prompt único, validação de anexos e upload opcional antes do envio
- `src/adapta/services/persona_service.py` -> validação do questionário de persona, leitura e escrita do JSON de respostas, montagem do prompt fixo, resolução dos caminhos de saída e cleanup best-effort do chat remoto
- `src/adapta/services/chat_service.py` -> fluxo de chat com limpeza remota e suporte a anexos enviados junto das mensagens
- `src/adapta/services/debate_service.py` -> orquestração do debate por rodadas, modo controlado com intervenções do usuário, leitura e gravação de configuração, suporte opcional a arquivo de persona por agente, upload único de anexos opcionais, conclusão final e emissão incremental
- `src/adapta/services/destilador_service.py` -> pipeline internalizado de destilação por 7 dimensões, com suporte a arquivo único e lote por diretório
- `src/adapta/services/pipeline_service.py` -> pipeline internalizado de extração e criação de conhecimentos, com varredura recursiva, índices JSON, escrita de markdown e persistência local em SQLite
- `src/adapta/services/output_service.py` -> escrita em stdout e arquivo
- `src/adapta/prompts/livro/*.txt` -> prompts internalizados das 7 dimensões usados pelo `destilador`
- `src/adapta/prompts/pipeline/*.txt` -> prompts internalizados de extração e criação usados pelo `pipeline`
- `scripts/install-local.sh` -> instala o comando `adapta` a partir do projeto local com `pipx` quando disponível ou fallback para `venv` dedicada
- `scripts/install-remote.sh` -> instala o comando `adapta` a partir de repositório remoto ou `file://`, com o mesmo fallback local de instalação
- `Makefile` -> atalhos para testes, prompt, chat e fluxos de instalação

## Fluxos principais

### Prompt

CLI -> resolução de configuração/modelo/anexos -> `prompt_service` -> upload opcional no cliente Adapta -> stdout/arquivo

### Chat

CLI -> resolução de configuração/modelo/anexos -> `chat_service` -> upload opcional no cliente Adapta -> loop de mensagens -> exclusão remota do chat

### Debate

CLI -> resolução de `--config` ou `ADAPTA_DEBATE_CONFIG` ou perguntas interativas -> parsing opcional de `--file` -> `debate_service` -> upload único opcional no cliente Adapta -> chats separados por agente ao longo das rodadas -> conclusão final -> stdout e/ou arquivo -> limpeza remota dos chats

### Persona

CLI -> perguntas interativas por bloco ou leitura de `--input-file` ou reedição por `--update` -> `persona_service` -> chat efêmero único no cliente Adapta com modelo padrão ou `--model` explícito -> markdown final + JSON de respostas -> escrita na pasta de personas do home do usuário -> limpeza remota best-effort

### Destilador

CLI -> resolução de `--input`/`--output`, `--input`/`--output-dir` ou `--input-dir`/`--output-dir` -> `destilador_service` -> upload do PDF ao Adapta -> geração de 7 dimensões com prompts internalizados -> consolidação markdown -> stdout e/ou arquivo -> preservação opcional de parciais -> limpeza best-effort dos artefatos

### Pipeline

CLI -> resolução de `--input-dir`, `--output-dir`, `--db-path` e ambiente -> `pipeline_service` -> descoberta recursiva de arquivos compatíveis -> SQLite local para jobs e conhecimentos -> upload dos arquivos ao Adapta -> geração de índice JSON e markdowns por conhecimento -> escrita de artefatos em `output-dir`

### Import-Cookies

CLI -> leitura de `session.json` ou export equivalente -> extração de cookies e `session_id` -> escrita em `~/.adapta/cookies.json`

### Models

CLI -> `registry` -> listagem ordenada de modelos -> stdout

### List Files

CLI -> cliente Adapta -> listagem paginada de arquivos remotos -> stdout tabulado

## Pontos críticos

- Autenticação: `src/adapta/client.py`
- Seleção de modelo: `src/adapta/registry.py`
- Logs por execução: `src/adapta/logging.py`
- Limpeza de chat remoto: `src/adapta/services/chat_service.py`
- Geração de persona: `src/adapta/services/persona_service.py`
- Orquestração multiagente: `src/adapta/services/debate_service.py`
- Pipeline de destilação: `src/adapta/services/destilador_service.py`
- Pipeline de conhecimentos: `src/adapta/services/pipeline_service.py`
- Prompts do destilador: `src/adapta/prompts/livro/*.txt`
- Prompts do pipeline: `src/adapta/prompts/pipeline/*.txt`
