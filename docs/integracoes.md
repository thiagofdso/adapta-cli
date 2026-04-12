# Integracoes

## Adapta

Tipo: API externa de autenticação e geração de respostas.

Autenticação:

- `ADAPTA_LOGIN`
- `ADAPTA_PASSWORD`

Uso principal:

- autenticar sessão
- enviar prompts e mensagens de chat
- enviar prompts e mensagens de chat com até 5 arquivos anexados por chamada de CLI
- reutilizar os mesmos anexos ao longo de todas as rodadas do comando `debate` quando iniciado com `--file`
- manter múltiplos chats simultâneos durante execuções de debate
- realizar upload de arquivos para processamento em fluxos como `destilador`
- listar arquivos remotos antes do upload para evitar duplicação por nome no `destilador`
- listar arquivos remotos sob demanda via comando `list-files`
- combinar arquivos enviados com prompts internalizados por dimensão no fluxo `destilador`
- excluir chats remotos ao término
- excluir artefatos remotos quando o pipeline terminar

Falhas possíveis:

- credenciais inválidas
- indisponibilidade temporária da API
- falha na limpeza do chat remoto
- falha no upload ou na exclusão de arquivo remoto

Restrições conhecidas:

- depende de conectividade externa
- o comportamento do backend pode variar por modelo
- debates com múltiplos agentes ampliam a quantidade de chamadas remotas por execução e exigem limpeza best-effort de todos os chats abertos
- destilações baseadas em arquivo ampliam o uso de upload remoto e exigem rastreamento explícito dos artefatos gerados
- o fluxo do `destilador` depende de o backend aceitar o PDF anexado no stream de chat e pode demandar execuções longas para documentos extensos

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
