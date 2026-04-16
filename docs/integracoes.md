# Integracoes

## Adapta

Tipo: API externa de autenticação e geração de respostas.

Autenticação:

- `ADAPTA_LOGIN`
- `ADAPTA_PASSWORD`

Uso principal:

- autenticar sessão
- reaproveitar cookies, `session_id` e cabeçalhos de autenticação salvos em `~/.adapta/cookies.json` para evitar novo login a cada execução
- importar export de cookies do navegador para `~/.adapta/cookies.json` via comando `import-cookies`
- enviar prompts e mensagens de chat
- enviar um prompt fixo de geração de persona em chat efêmero via comando `persona`, usando o modelo padrão ou um `--model` explícito do usuário
- enviar prompts e mensagens de chat com até 5 arquivos anexados por chamada de CLI
- reutilizar os mesmos anexos ao longo de todas as rodadas do comando `debate` quando iniciado com `--file`
- manter múltiplos chats simultâneos durante execuções de debate, inclusive com agentes da mesma rodada em paralelo no modo normal
- realizar upload de arquivos para processamento em fluxos como `destilador`, exceto quando a entrada é `.txt` e o conteúdo segue inline no prompt
- realizar upload de arquivos para processamento no comando `pipeline`, exceto quando a entrada é `.txt` e o conteúdo segue inline no prompt
- listar arquivos remotos antes do upload para evitar duplicação por nome no `destilador`
- listar arquivos remotos sob demanda via comando `list-files`
- combinar arquivos enviados com prompts internalizados por dimensão no fluxo `destilador`
- combinar arquivos enviados com prompts internalizados de extração e criação no fluxo `pipeline`
- absorver rajadas moderadas de chamadas paralelas vindas do `destilador` por item e do `pipeline` na etapa de geração de markdown
- excluir chats remotos ao término
- excluir o chat remoto ao término do comando `persona`, com aviso operacional se a limpeza falhar após o salvamento local
- excluir artefatos remotos quando o pipeline terminar

Falhas possíveis:

- credenciais inválidas
- indisponibilidade temporária da API
- falha na limpeza do chat remoto
- falha no upload ou na exclusão de arquivo remoto

Restrições conhecidas:

- depende de conectividade externa
- o comportamento do backend pode variar por modelo
- quando a sessão persistida expira ou recebe `401`, a CLI descarta `~/.adapta/cookies.json`, executa novo login e regrava o cache local
- a CLI só invalida explicitamente a sessão local ao encerrar quando `ADAPTA_LOGOUT=true`; em qualquer outro caso, o cache permanece disponível para reaproveitamento
- debates com múltiplos agentes ampliam a quantidade de chamadas remotas por execução e exigem limpeza best-effort de todos os chats abertos
- destilações baseadas em arquivo ampliam o uso de upload remoto e exigem rastreamento explícito dos artefatos gerados; no modo por diretório, múltiplos itens podem ser processados em paralelo
- o fluxo do `pipeline` amplia o uso de upload remoto e exige rastreamento local em SQLite para jobs, conhecimentos e artefatos por diretório; a etapa 2 aumenta a concorrência remota ao gerar múltiplos markdowns em paralelo
- o fluxo do `destilador` depende de o backend aceitar o PDF anexado no stream de chat e pode demandar execuções longas para documentos extensos

## SQLite local do pipeline

Tipo: persistência operacional local.

Uso principal:

- registrar jobs descobertos no diretório de entrada
- persistir conhecimentos pendentes e concluídos ao longo da execução
- permitir retomar rastreamento por job quando o usuário informar `--job`

Falhas possíveis:

- caminho sem permissão de escrita
- arquivo corrompido ou incompatível
- diretório pai inexistente sem possibilidade de criação

Comportamento operacional:

- o caminho padrão é `~/.local/state/adapta-cli/pipeline.db`
- a variável `ADAPTA_PIPELINE_DB_PATH` substitui o padrão
- a opção `--db-path` tem precedência sobre ambiente e padrão

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
