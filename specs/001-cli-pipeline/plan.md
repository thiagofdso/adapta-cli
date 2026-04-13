# Implementation Plan: Comando pipeline por diretório

**Branch**: `[001-build-adapta-cli]` | **Date**: 2026-04-13 | **Spec**: [/mnt/c/whatsweb/adapta-cli/specs/001-cli-pipeline/spec.md](/mnt/c/whatsweb/adapta-cli/specs/001-cli-pipeline/spec.md)
**Input**: Feature specification from `/specs/001-cli-pipeline/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Adicionar o comando `adapta pipeline` para processar diretórios de entrada e saída configuráveis, preservando o comportamento funcional do pipeline legado e internalizando sua orquestração dentro da CLI. O desenho adotará um serviço local dedicado, banco SQLite semelhante ao original com caminho padrão e sobrescrita por ambiente ou parâmetro explícito, além de contrato de CLI alinhado aos padrões já usados por `debate` e `destilador`.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11  
**Primary Dependencies**: Typer, httpx, python-dotenv, pytest, biblioteca padrão `sqlite3`  
**Storage**: SQLite local para estado operacional do pipeline e filesystem para artefatos de saída  
**Testing**: pytest com testes unitários de resolução/configuração e testes de integração da CLI  
**Target Platform**: CLI local em Linux com comportamento instalável fora do repositório  
**Project Type**: CLI  
**Performance Goals**: iniciar processamento sem interação adicional e manter processamento em lote recursivo com comportamento equivalente ao pipeline legado para diretórios pequenos e médios  
**Constraints**: sem dependência de código-fonte externo em runtime; manter formato funcional de entrada e saída do pipeline original; falhar cedo para diretórios ou banco inválidos; respeitar precedência `--db-path` > ambiente > padrão  
**Scale/Scope**: um novo comando de CLI, um novo serviço interno de pipeline, integração com SQLite local, suporte a processamento recursivo de arquivos compatíveis e documentação completa em `docs/`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate 1 - Documentation-first**: PASS. Foram consultados `docs/features.md`, `docs/arquitetura.md`, `docs/code-map.md`, `docs/modelo-dados.md`, `docs/integracoes.md`, `docs/licoes-aprendidas.md` e ADR existente antes do plano.
- **Gate 2 - Architecture decisions recorded**: PASS WITH FOLLOW-UP. O plano prevê novo ADR para a decisão de internalizar o pipeline legado com persistência SQLite local configurável.
- **Gate 3 - Test-first delivery**: PASS. O plano exige atualização de documentação antes de testes e implementação, seguida de TDD para serviço, configuração e contrato do comando.
- **Gate 4 - Integration and operational validation**: PASS. O plano inclui validação de CLI, configuração de banco, diretórios, comportamento de saída e interações externas relevantes do fluxo.
- **Gate 5 - Simplicity and consistency**: PASS. A solução proposta reaproveita padrões existentes da CLI, evita runtime externo e adiciona apenas o mínimo necessário: um comando, um serviço e persistência local explícita.

**Post-Design Re-Check**:

- PASS. `research.md` resolveu as decisões técnicas sem deixar pendências abertas.
- PASS. `data-model.md` cobre entidades operacionais, banco local e rastreabilidade de artefatos.
- PASS. `contracts/pipeline-command.md` define o contrato do comando, precedência de configuração e regras de validação.
- PASS. `quickstart.md` cobre uso mínimo, customização por ambiente e parâmetro explícito.

**Documentation Impact**:

- `docs/features.md`: adicionar a feature `pipeline` com contrato de entrada por diretório, saída por diretório e configuração de banco.
- `docs/code-map.md`: adicionar o novo comando na CLI e o serviço responsável pela orquestração.
- `docs/arquitetura.md`: registrar o novo fluxo operacional e o uso de persistência SQLite local do pipeline.
- `docs/modelo-dados.md`: adicionar as entidades operacionais do pipeline e a configuração de banco.
- `docs/integracoes.md`: refletir o uso do backend Adapta e do SQLite local no novo fluxo.
- `docs/licoes-aprendidas.md`: registrar qualquer incidente relevante durante a internalização, especialmente caminhos, limpeza e compatibilidade.
- `docs/adr/`: planejar um novo ADR para a decisão arquitetural de internalizar o pipeline legado com persistência SQLite local configurável.

## Project Structure

### Documentation (this feature)

```text
specs/001-cli-pipeline/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── pipeline-command.md
└── tasks.md
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
docs/
├── code-map.md
├── arquitetura.md
├── adr/
├── features.md
├── modelo-dados.md
├── integracoes.md
├── licoes-aprendidas.md
└── guia-uso-documentacao.md

src/
└── adapta/
    ├── cli.py
    ├── config.py
    ├── models.py
    ├── client.py
    ├── prompts/
    │   └── pipeline/
    └── services/
        └── pipeline_service.py

tests/
├── unit/
│   ├── test_cli.py
│   ├── test_config.py
│   └── test_pipeline_service.py
└── integration/
    └── test_pipeline_command.py
```

**Structure Decision**: Manter a estrutura atual de projeto único em `src/adapta`, adicionando um serviço dedicado para o pipeline e prompts internalizados específicos quando necessário. Os testes seguem a convenção atual de `tests/unit` e `tests/integration`, sem introduzir novas camadas ou subprojetos.

## Complexity Tracking

Nenhuma violação prevista no plano.
