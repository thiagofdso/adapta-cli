# Integracoes

## Adapta

Tipo: API externa de autenticação e geração de respostas.

Autenticação:

- `ADAPTA_LOGIN`
- `ADAPTA_PASSWORD`

Uso principal:

- autenticar sessão
- enviar prompts e mensagens de chat
- manter múltiplos chats simultâneos durante execuções de debate
- excluir chats remotos ao término

Falhas possíveis:

- credenciais inválidas
- indisponibilidade temporária da API
- falha na limpeza do chat remoto

Restrições conhecidas:

- depende de conectividade externa
- o comportamento do backend pode variar por modelo
- debates com múltiplos agentes ampliam a quantidade de chamadas remotas por execução e exigem limpeza best-effort de todos os chats abertos

## Repositório remoto para instalação

Tipo: origem remota para instalação da CLI.

Uso principal:

- instalar o projeto a partir de uma URL remota usando o script de instalação.
- permitir instalação por referência opcional ou origem local no formato `file://`.

Falhas possíveis:

- URL inválida
- indisponibilidade do repositório
- falha de instalação do pacote

Comportamento operacional:

- os scripts tentam usar `pipx` primeiro, depois `python -m pipx` quando disponível.
- se `pipx` não estiver disponível, a instalação cai para uma `venv` dedicada em `~/.local/share/adapta-cli/venv`.
- o comando final `adapta` é exposto por link simbólico em `~/.local/bin/adapta`.
