# Code Map

## Estrutura

- `src/adapta/cli.py` -> comandos Typer, parsing da linha de comando e listagem de modelos
- `src/adapta/config.py` -> carregamento de `.env` e configurações tipadas
- `src/adapta/logging.py` -> configuração de logs por execução
- `src/adapta/registry.py` -> catálogo de modelos e resolução de aliases
- `src/adapta/runtime.py` -> ponte síncrona para fluxos assíncronos
- `src/adapta/client.py` -> cliente interno do Adapta com classes focadas em sessão HTTP, autenticação e conversas
- `src/adapta/services/prompt_service.py` -> fluxo de prompt único
- `src/adapta/services/chat_service.py` -> fluxo de chat com limpeza remota
- `src/adapta/services/output_service.py` -> escrita em stdout e arquivo
- `scripts/install-local.sh` -> instala o comando `adapta` a partir do projeto local com `pipx` quando disponível ou fallback para `venv` dedicada
- `scripts/install-remote.sh` -> instala o comando `adapta` a partir de repositório remoto ou `file://`, com o mesmo fallback local de instalação
- `Makefile` -> atalhos para testes, prompt, chat e fluxos de instalação

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
