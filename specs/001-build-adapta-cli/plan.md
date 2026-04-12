# Implementation Plan: Build Adapta CLI

**Branch**: `[001-build-adapta-cli]` | **Date**: 2026-04-12 | **Spec**: [/mnt/c/whatsweb/adapta-cli/specs/001-build-adapta-cli/spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-build-adapta-cli/spec.md`

## Summary

Construir uma CLI Python empacotada com `pyproject.toml` para executar prompts únicos e chat com os modelos do Adapta, reutilizando o comportamento essencial de autenticação, roteamento de modelos e ciclo de vida de chat do projeto existente. A implementação seguirá uma abordagem doc-first com TDD: primeiro documentar o impacto negocial e técnico em `docs/`, depois escrever os testes unitários para regras de CLI, orquestração, instalação, `Makefile` e configuração de logs, depois implementação mínima para passar, e por fim testes de integração com chamadas reais usando `.env` local e prompts simples como validação determinística. O projeto também terá scripts de instalação para disponibilizar `adapta` como comando do sistema tanto a partir dos arquivos locais quanto a partir de um repositório remoto. O comportamento padrão da CLI será sem logs operacionais, ativando logs apenas quando a pessoa usuária informar `--log info` ou `--log debug`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Typer, httpx, pydantic-settings, python-dotenv, pytest  
**Storage**: Arquivos locais para `.env`, prompts de entrada e arquivos opcionais de saída; sessões de chat remotas temporárias no Adapta  
**Testing**: pytest com testes unitários isolados e testes de integração via execução real da CLI  
**Target Platform**: Terminal local em Linux, macOS e Windows  
**Project Type**: CLI Python empacotada em projeto único  
**Performance Goals**: Comandos de validação local devem falhar ou iniciar em até 2 segundos antes da espera de rede; operações de arquivo devem concluir na mesma execução do comando  
**Constraints**: Reutilizar autenticação baseada em `ADAPTA_LOGIN` e `ADAPTA_PASSWORD`; carregar `.env` do próprio projeto CLI; usar `ADAPTA_MODEL` como padrão; excluir o chat remoto ao final de cada sessão; manter a interface simples e orientada a terminal; não emitir logs por padrão; ativar logs apenas por parâmetro com níveis como `info` e `debug`; disponibilizar instalação local e remota do comando `adapta`; incluir `Makefile` com atalhos de uso e testes  
**Scale/Scope**: Uma pessoa usuária por processo, um chat ativo por vez, suporte aos modelos já disponíveis no Adapta atual

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- O arquivo `/mnt/c/whatsweb/adapta-cli/.specify/memory/constitution.md` ainda contém apenas placeholders e não define regras obrigatórias acionáveis.
- Gates provisórios aplicados a esta feature com base no pedido do usuário:
- Doc-first é obrigatório: documentar impacto negocial e técnico antes de criar testes ou implementação.
- TDD é obrigatório após a documentação inicial: escrever testes unitários antes da implementação.
- Testes de integração só entram após a suíte unitária estar verde.
- A solução deve permanecer em um único projeto Python simples, sem camadas desnecessárias.
- Status pré-pesquisa: aprovado.
- Status pós-design: aprovado; os artefatos preservam um projeto único, fluxo test-first e contrato de CLI enxuto.

## Project Structure

### Documentation (this feature)

```text
specs/001-build-adapta-cli/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cli-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
pyproject.toml
.env
Makefile
scripts/
├── install-local.sh
└── install-remote.sh
src/
└── adapta/
    ├── __init__.py
    ├── __main__.py
    ├── cli.py
    ├── config.py
    ├── logging.py
    ├── models.py
    ├── registry.py
    ├── runtime.py
    ├── client.py
    └── services/
        ├── __init__.py
        ├── prompt_service.py
        ├── chat_service.py
        └── output_service.py

tests/
├── unit/
│   ├── test_config.py
│   ├── test_registry.py
│   ├── test_prompt_service.py
│   ├── test_chat_service.py
│   ├── test_cli.py
│   ├── test_logging.py
│   ├── test_install_scripts.py
│   └── test_makefile.py
└── integration/
    ├── test_prompt_command.py
    ├── test_prompt_file_command.py
    ├── test_output_file_command.py
    ├── test_chat_cleanup.py
    └── test_installation_flow.py
```

**Structure Decision**: Adotar layout `src/` com uma camada fina de CLI e serviços separados para prompt, chat e saída. O cliente Adapta, o registro de modelos e a configuração de logs ficam centralizados para reaproveitar o mesmo comportamento de autenticação e resolução de modelo sem replicar a estrutura `generators_v2` literalmente. Scripts dedicados de instalação ficam em `scripts/` para cobrir uso local e instalação a partir de repositório remoto, enquanto o `Makefile` concentra os atalhos de desenvolvimento e execução rápida.

## Documentation Impact

- `docs/features.md`: descrever a nova feature da CLI, seus comandos principais e status.
- `docs/code-map.md`: mapear a nova estrutura `src/adapta/`, `scripts/`, `Makefile` e fluxos principais de prompt e chat.
- `docs/arquitetura.md`: registrar a arquitetura da CLI, dependência do Adapta e a abordagem doc-first com TDD.
- `docs/modelo-dados.md`: documentar entidades de configuração, modelos, requisições de prompt e sessões de chat.
- `docs/integracoes.md`: descrever autenticação e chamadas ao Adapta, além do fluxo de instalação remota.
- `docs/licoes-aprendidas.md`: registrar erros relevantes de integração, autenticação, empacotamento ou limpeza de chat encontrados durante a implementação.
- `docs/adr/`: criar ADR se houver decisão arquitetural relevante sobre reaproveitamento do cliente Adapta, estratégia de empacotamento ou instalação.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Nenhuma | N/A | N/A |
