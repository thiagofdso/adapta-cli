# Arquitetura

## Estilo arquitetural

Projeto único em Python, empacotado como CLI e organizado em camadas leves de comando, serviços e integração externa.

## Componentes principais

- CLI Typer para `prompt` e `chat`
- módulo de configuração baseado em `.env`
- registro de modelos para mapear aliases curtos para nomes do backend Adapta
- cliente HTTP assíncrono interno reestruturado em camadas de sessão, autenticação e conversas
- serviços separados para prompt, chat e persistência de saída

## Comunicação entre componentes

- comandos de CLI recebem opções, resolvem configuração e delegam para serviços
- serviços orquestram chamadas ao cliente Adapta e retornam respostas normalizadas
- o cliente encapsula autenticação, envio de prompts e exclusão de chats em classes com objetivos específicos

## Tecnologias

- Python 3.11
- Typer
- httpx
- pydantic-settings
- python-dotenv
- pytest

## Trade-offs conhecidos

- a CLI privilegia simplicidade e um único processo por sessão
- logs são opt-in para manter saída limpa no uso comum
- chat é efêmero: a sessão remota é excluída ao final por requisito do produto
- a implementação atual internaliza apenas o subconjunto necessário do cliente do Adapta para prompt, chat e limpeza remota, reduzindo dependências externas do projeto
