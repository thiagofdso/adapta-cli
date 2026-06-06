# Implementation Plan: Debate no CLI

**Branch**: `[001-build-adapta-cli]` | **Date**: 2026-04-12 | **Spec**: [`/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/spec.md`]  
**Input**: Feature specification from `/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/spec.md`

## Summary

Adicionar um comando `debate` ao CLI para orquestrar múltiplos agentes com configuração por arquivo, variável de ambiente ou perguntas interativas, reutilizando os padrões atuais de seleção de modelo, chat remoto, saída em terminal e persistência opcional em arquivo. O desenho prioriza um novo serviço de debate com sessões de chat separadas por agente, execução por rodadas, conclusão consolidada e limpeza remota consistente com o comando `chat`.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Typer, httpx, python-dotenv, pytest  
**Storage**: arquivos locais JSON e texto/markdown para configuração e saída; estado remoto efêmero de chat no serviço Adapta  
**Testing**: pytest com testes unitários via `CliRunner` e testes de integração via `subprocess`  
**Target Platform**: CLI local para Linux, macOS e Windows com Python 3.11  
**Project Type**: single-package CLI  
**Performance Goals**: iniciar debates válidos sem preparação manual extra; exibir cada resposta concluída imediatamente no terminal quando não houver `--output`; concluir a configuração interativa inicial em até 3 minutos  
**Constraints**: preservar erros curtos sem traceback; evitar dependência de código-fonte externo em runtime; manter limpeza best-effort dos chats remotos; validar entradas numéricas antes de iniciar o debate  
**Scale/Scope**: execução por um operador local, com pequeno conjunto de agentes e rodadas por execução, um modelo de conclusão por debate e um artefato final por execução

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Documentation-First Development**: PASS. O contexto funcional e arquitetural já foi consultado em `docs/features.md`, `docs/arquitetura.md`, `docs/code-map.md`, `docs/modelo-dados.md`, `docs/integracoes.md`, `docs/licoes-aprendidas.md` e `docs/adr/ADR-001-cli-packaging.md`.
- **Architecture Decisions Must Be Recorded**: PASS. O plano mantém a arquitetura existente de CLI fina + serviços; nenhum novo ADR é necessário neste estágio, mas a necessidade será reavaliada se a orquestração multiagente exigir nova abstração estrutural.
- **Documentation-First and Test-First Delivery**: PASS. A execução prevista segue documentação em `docs/` antes de testes e implementação; testes unitários e de integração serão planejados antes do código.
- **Integration and Operational Validation**: PASS. O recurso afeta autenticação, múltiplos chats remotos, cleanup e persistência local, então o plano inclui validação explícita desses fluxos e atualização de quickstart.
- **Simplicity, Consistency, and Learning**: PASS. A proposta adiciona um serviço dedicado de debate e modelos mínimos de domínio, reaproveitando `registry`, `chat_service`, `output_service` e os padrões atuais de CLI.

**Documentation Impact**:

- `docs/features.md`: adicionar a feature `debate` e suas formas de entrada.
- `docs/code-map.md`: registrar o novo comando, serviço e fluxos por rodada.
- `docs/arquitetura.md`: descrever a orquestração multiagente dentro da CLI existente.
- `docs/modelo-dados.md`: incluir entidades de configuração, rodada, turno e resultado do debate.
- `docs/integracoes.md`: detalhar o uso ampliado da API Adapta para múltiplos chats e cleanup final.
- `docs/licoes-aprendidas.md`: registrar incidentes relevantes de validação, cleanup ou ordenação de saída quando surgirem na implementação.
- `docs/adr/`: nenhum novo ADR planejado no momento.

**Post-Design Re-Check**:

- PASS. O design em `research.md`, `data-model.md`, `contracts/` e `quickstart.md` continua alinhado à constituição, sem novas violações ou dependências estruturais não justificadas.

## Project Structure

### Documentation (this feature)

```text
specs/003-add-cli-debate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── debate-command.md
└── tasks.md
```

### Source Code (repository root)

```text
docs/
├── adr/
├── arquitetura.md
├── code-map.md
├── features.md
├── guia-uso-documentacao.md
├── integracoes.md
├── licoes-aprendidas.md
└── modelo-dados.md

src/
└── adapta/
    ├── cli.py
    ├── client.py
    ├── config.py
    ├── models.py
    ├── registry.py
    ├── runtime.py
    └── services/
        ├── chat_service.py
        ├── output_service.py
        ├── prompt_service.py
        └── debate_service.py

tests/
├── integration/
│   ├── test_debate_command.py
│   └── test_debate_output_file.py
└── unit/
    ├── test_cli.py
    ├── test_debate_service.py
    └── test_registry.py
```

**Structure Decision**: Manter a estrutura única do projeto e introduzir apenas `src/adapta/services/debate_service.py`, ampliando `src/adapta/models.py` e `src/adapta/cli.py` para preservar o padrão atual de comandos finos e serviços de orquestração.

## Complexity Tracking

Nenhuma violação de constituição ou complexidade excepcional identificada neste planejamento.
