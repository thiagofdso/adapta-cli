# Integracoes

## Adapta

Tipo: API externa de autenticação e geração de respostas.

Autenticação:

- `ADAPTA_LOGIN`
- `ADAPTA_PASSWORD`

Uso principal:

- autenticar sessão
- enviar prompts e mensagens de chat
- excluir chats remotos ao término

Falhas possíveis:

- credenciais inválidas
- indisponibilidade temporária da API
- falha na limpeza do chat remoto

Restrições conhecidas:

- depende de conectividade externa
- o comportamento do backend pode variar por modelo

## Repositório remoto para instalação

Tipo: origem remota para instalação da CLI.

Uso principal:

- instalar o projeto a partir de uma URL remota usando o script de instalação.

Falhas possíveis:

- URL inválida
- indisponibilidade do repositório
- falha de instalação do pacote
