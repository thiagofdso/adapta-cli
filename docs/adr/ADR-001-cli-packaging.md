# ADR-001 - Internalizar um cliente mínimo do Adapta

## Contexto

A CLI precisa usar os mesmos modelos e o mesmo fluxo de autenticação do projeto Adapta, mas sem depender do código-fonte externo em tempo de execução.

## Decisao

Internalizar na CLI um cliente mínimo, reestruturado em classes menores, cobrindo apenas autenticação, prompt, chat e exclusão de conversas.

## Consequencias

+ elimina a dependência de código-fonte externo em tempo de execução
+ melhora a legibilidade ao separar sessão HTTP, autenticação e conversas
- aumenta a responsabilidade local de manutenção do cliente compatível com o Adapta
