# ADR-002 - Internalizar o pipeline de conhecimentos na CLI

## Contexto

O projeto precisa expor um comando `pipeline` compatível com o fluxo legado de extração e geração de conhecimentos por diretório, mas sem depender do código-fonte do outro repositório em tempo de execução.

## Decisao

Internalizar na CLI um serviço dedicado de pipeline que preserve o formato funcional de entrada e saída do fluxo legado, use prompts copiados localmente e persista estado operacional em SQLite local configurável por padrão, ambiente e opção explícita.

## Consequencias

+ elimina o acoplamento de runtime com outro repositório
+ mantém previsibilidade operacional para quem já usa o pipeline legado
+ permite testes unitários e de integração dentro da própria CLI
- aumenta a responsabilidade local de manter prompts, SQLite e regras de merge de índice compatíveis com o legado
