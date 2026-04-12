# Code Map

## Estrutura

- `src/adapta/cli.py` -> comandos Typer e parsing da linha de comando
- `src/adapta/config.py` -> carregamento de `.env` e configurações tipadas
- `src/adapta/logging.py` -> configuração de logs por execução
- `src/adapta/registry.py` -> catálogo de modelos e resolução de aliases
- `src/adapta/runtime.py` -> ponte síncrona para fluxos assíncronos
- `src/adapta/client.py` -> cliente interno do Adapta com classes focadas em sessão HTTP, autenticação e conversas
- `src/adapta/services/prompt_service.py` -> fluxo de prompt único
- `src/adapta/services/chat_service.py` -> fluxo de chat com limpeza remota
- `src/adapta/services/output_service.py` -> escrita em stdout e arquivo
- `scripts/install-local.sh` -> instalação local do comando `adapta`
- `scripts/install-remote.sh` -> instalação remota do comando `adapta`
- `Makefile` -> atalhos para testes, prompt e chat

## Fluxos principais

### Prompt

CLI -> resolução de configuração/modelo -> `prompt_service` -> cliente Adapta -> stdout/arquivo

### Chat

CLI -> resolução de configuração/modelo -> `chat_service` -> cliente Adapta -> loop de mensagens -> exclusão remota do chat

## Pontos críticos

- Autenticação: `src/adapta/client.py`
- Seleção de modelo: `src/adapta/registry.py`
- Logs por execução: `src/adapta/logging.py`
- Limpeza de chat remoto: `src/adapta/services/chat_service.py`
