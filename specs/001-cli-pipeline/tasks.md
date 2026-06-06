# Tasks: Comando pipeline por diretório

**Input**: Design documents from `/specs/001-cli-pipeline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Testes incluídos. A constituição e o plano exigem TDD para implementação.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths for this feature follow the structure defined in `specs/001-cli-pipeline/plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar documentação, estrutura base e pontos de extensão do comando antes de qualquer teste ou implementação

- [X] T001 Atualizar a descrição da feature `pipeline` em `docs/features.md`
- [X] T002 [P] Atualizar o fluxo do novo comando em `docs/code-map.md`
- [X] T003 [P] Atualizar a arquitetura com o serviço `pipeline` e SQLite local em `docs/arquitetura.md`
- [X] T004 [P] Atualizar entidades operacionais do pipeline em `docs/modelo-dados.md`
- [X] T005 [P] Atualizar integração do pipeline com Adapta e SQLite local em `docs/integracoes.md`
- [X] T006 Criar ADR para internalização do pipeline legado e persistência SQLite em `docs/adr/ADR-002-cli-pipeline.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestrutura central que bloqueia todas as user stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Adicionar modelos `PipelineRequest`, `PipelineRun` e artefatos correlatos em `src/adapta/models.py`
- [X] T008 [P] Adicionar resolução de caminho padrão e por ambiente para o banco do pipeline em `src/adapta/config.py`
- [X] T009 [P] Criar testes unitários de configuração e precedência do banco em `tests/unit/test_config.py`
- [X] T010 [P] Criar contrato do comando `pipeline` em testes de CLI em `tests/unit/test_cli.py`
- [X] T011 Implementar infraestrutura SQLite do pipeline em `src/adapta/services/pipeline_service.py`
- [X] T012 Implementar prompts e recursos internalizados do pipeline em `src/adapta/prompts/pipeline/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Executar pipeline em lote por diretório (Priority: P1) 🎯 MVP

**Goal**: Permitir execução do pipeline completo por `--input-dir` e `--output-dir`, com varredura recursiva e compatibilidade funcional com o fluxo legado

**Independent Test**: Executar `adapta pipeline --input-dir <dir> --output-dir <dir>` com arquivos compatíveis e verificar artefatos equivalentes ao pipeline legado apenas no diretório de saída informado.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Adicionar teste de integração do comando por diretório em `tests/integration/test_pipeline_command.py`
- [X] T014 [P] [US1] Adicionar teste unitário de descoberta recursiva e montagem de request em `tests/unit/test_pipeline_service.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implementar descoberta recursiva de documentos e normalização de itens em `src/adapta/services/pipeline_service.py`
- [X] T016 [P] [US1] Implementar persistência de jobs e conhecimentos em SQLite em `src/adapta/services/pipeline_service.py`
- [X] T017 [US1] Implementar orquestração principal do pipeline compatível com o legado em `src/adapta/services/pipeline_service.py`
- [X] T018 [US1] Expor o comando `pipeline` com `--input-dir` e `--output-dir` em `src/adapta/cli.py`
- [X] T019 [US1] Integrar resumo de sucesso e destinos produzidos no comando em `src/adapta/cli.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Controlar destino dos artefatos gerados (Priority: P2)

**Goal**: Garantir isolamento e previsibilidade do diretório de saída, preservando a estrutura funcional de artefatos do pipeline

**Independent Test**: Executar duas vezes o comando com o mesmo `input-dir` e `output-dir` distintos e confirmar que cada execução grava artefatos somente em seu destino.

### Tests for User Story 2 ⚠️

- [X] T020 [P] [US2] Adicionar teste de integração para isolamento de `output-dir` em `tests/integration/test_pipeline_command.py`
- [X] T021 [P] [US2] Adicionar teste unitário de caminhos e artefatos gerados em `tests/unit/test_pipeline_service.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Implementar resolução de caminhos de índices e artefatos dentro de `output-dir` em `src/adapta/services/pipeline_service.py`
- [X] T023 [US2] Implementar escrita dos artefatos compatíveis com o legado em `src/adapta/services/pipeline_service.py`
- [X] T024 [US2] Garantir rastreabilidade entre documento processado e artefatos produzidos em `src/adapta/services/pipeline_service.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Configurar o banco operacional do pipeline (Priority: P2)

**Goal**: Permitir uso do banco SQLite com caminho padrão, variável de ambiente e parâmetro explícito com precedência determinística

**Independent Test**: Executar o comando sem configuração, com `ADAPTA_PIPELINE_DB_PATH` e com `--db-path`, verificando o caminho efetivamente usado em cada cenário.

### Tests for User Story 3 ⚠️

- [X] T025 [P] [US3] Adicionar teste unitário da precedência `--db-path` > ambiente > padrão em `tests/unit/test_config.py`
- [X] T026 [P] [US3] Adicionar teste de integração do comando com banco customizado em `tests/integration/test_pipeline_command.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implementar resolução final de `db_path` no request do pipeline em `src/adapta/services/pipeline_service.py`
- [X] T028 [US3] Adicionar a opção `--db-path` e repasse do caminho resolvido em `src/adapta/cli.py`
- [X] T029 [US3] Validar criação, acesso e mensagens de erro para banco inválido em `src/adapta/services/pipeline_service.py`

**Checkpoint**: At this point, User Stories 1, 2 AND 3 should work independently

---

## Phase 6: User Story 4 - Receber feedback de execução e falhas de entrada (Priority: P3)

**Goal**: Emitir mensagens curtas e acionáveis para início, sucesso e falhas esperadas de diretório, lote vazio e banco sem permissão

**Independent Test**: Executar o comando com diretório inexistente, diretório sem arquivos compatíveis e banco sem permissão, verificando mensagens distintas e saída com código `1`.

### Tests for User Story 4 ⚠️

- [X] T030 [P] [US4] Adicionar testes unitários de falhas esperadas do pipeline em `tests/unit/test_pipeline_service.py`
- [X] T031 [P] [US4] Adicionar testes de CLI para mensagens curtas e código de erro em `tests/unit/test_cli.py`

### Implementation for User Story 4

- [X] T032 [P] [US4] Implementar validações de entrada e lote vazio em `src/adapta/services/pipeline_service.py`
- [X] T033 [P] [US4] Implementar mensagens de progresso e resumo operacional em `src/adapta/services/pipeline_service.py`
- [X] T034 [US4] Adaptar tratamento de erro do comando `pipeline` em `src/adapta/cli.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Fechamento final, validação operacional e documentação de aprendizado

- [X] T035 [P] Validar os cenários documentados em `specs/001-cli-pipeline/quickstart.md`
- [X] T036 [P] Registrar incidentes ou armadilhas encontradas em `docs/licoes-aprendidas.md`
- [X] T037 Executar a suíte relevante de testes em `tests/unit/test_config.py`, `tests/unit/test_cli.py`, `tests/unit/test_pipeline_service.py` e `tests/integration/test_pipeline_command.py`
- [X] T038 Executar revisão final de limpeza e consistência em `src/adapta/cli.py`, `src/adapta/config.py`, `src/adapta/models.py` e `src/adapta/services/pipeline_service.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - MVP slice
- **User Story 2 (P2)**: Depends on US1 orchestration existing, but remains independently testable by validating output isolation
- **User Story 3 (P2)**: Depends on foundational config and pipeline request wiring, but remains independently testable by validating DB resolution
- **User Story 4 (P3)**: Depends on the command existing and service validations being wired, but remains independently testable via expected failures

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Request/config models before orchestration wiring
- Service behavior before CLI integration
- CLI integration before end-to-end validation

### Parallel Opportunities

- `T002`, `T003`, `T004` and `T005` can run in parallel after `T001`
- `T007`, `T008`, `T009` and `T010` can run in parallel in Phase 2
- `T013` and `T014` can run in parallel for US1
- `T020` and `T021` can run in parallel for US2
- `T025` and `T026` can run in parallel for US3
- `T030` and `T031` can run in parallel for US4

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Add integration test for directory pipeline flow in tests/integration/test_pipeline_command.py"
Task: "Add recursive discovery unit test in tests/unit/test_pipeline_service.py"

# Launch independent implementation tasks for User Story 1 together:
Task: "Implement document discovery in src/adapta/services/pipeline_service.py"
Task: "Implement SQLite job persistence in src/adapta/services/pipeline_service.py"
```

## Parallel Example: User Story 3

```bash
# Launch DB configuration tests together:
Task: "Add db precedence unit test in tests/unit/test_config.py"
Task: "Add custom db path integration test in tests/integration/test_pipeline_command.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational
2. Add User Story 1 and validate MVP
3. Add User Story 2 for output isolation
4. Add User Story 3 for DB customization
5. Add User Story 4 for operator-facing feedback and expected failures

### Parallel Team Strategy

1. One developer updates mandatory docs and ADR in Phase 1 while another prepares foundational tests
2. After Foundation, one developer can focus on service behavior and another on CLI/tests
3. P2 stories can proceed in parallel once US1 service orchestration is stable

---

## Notes

- [P] tasks = different files or logically separable work with no dependency on an unfinished task
- [Story] label maps each implementation slice to a specific user story
- Every user story has explicit independent test criteria
- Documentation and ADR work are scheduled before tests and code to satisfy the constitution
- All task lines follow the required checklist format with ID, optional markers, story label when applicable, and exact file paths
