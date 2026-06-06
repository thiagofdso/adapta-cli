# Tasks: Destilador no CLI

**Input**: Design documents from `/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/`
**Prerequisites**: `/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/plan.md`, `/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/spec.md`, `/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/research.md`, `/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/data-model.md`, `/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/contracts/destilador-command.md`

**Tests**: TDD obrigatório por constituição do repositório. Cada história inclui testes antes da implementação.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Documentation)

**Purpose**: Atualizar a documentação obrigatória antes de testes e implementação

- [ ] T001 Update `destilador` feature map for file and directory modes in /mnt/c/whatsweb/adapta-cli/docs/features.md
- [ ] T002 [P] Update command flow and internalized pipeline map in /mnt/c/whatsweb/adapta-cli/docs/code-map.md
- [ ] T003 [P] Update CLI architecture for internalized distillation flow in /mnt/c/whatsweb/adapta-cli/docs/arquitetura.md
- [ ] T004 [P] Add distillation request, batch, dimension and artifact entities in /mnt/c/whatsweb/adapta-cli/docs/modelo-dados.md
- [ ] T005 [P] Document file listing, deduplicated upload, remote processing and cleanup behavior for `destilador` in /mnt/c/whatsweb/adapta-cli/docs/integracoes.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared structures and pipeline building blocks required before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Add distillation request, input item, dimension, artifact and result models in /mnt/c/whatsweb/adapta-cli/src/adapta/models.py
- [ ] T007 [P] Extend the Adapta client interface for file-oriented distillation operations, remote file listing and upload deduplication in /mnt/c/whatsweb/adapta-cli/src/adapta/client.py
- [ ] T008 [P] Add distillation output formatting and persistence helpers in /mnt/c/whatsweb/adapta-cli/src/adapta/services/output_service.py
- [ ] T009 Create internalized distillation pipeline scaffold in /mnt/c/whatsweb/adapta-cli/src/adapta/services/destilador_service.py
- [ ] T010 Register the `destilador` command skeleton and shared parameter validation in /mnt/c/whatsweb/adapta-cli/src/adapta/cli.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Destilar uma entrada informada pelo usuário (Priority: P1) 🎯 MVP

**Goal**: Permitir processar um arquivo individual com `--input` e `--output` e também um lote com `--input-dir` e `--output-dir`, gerando o consolidado final correto.

**Independent Test**: Executar `adapta destilador` em modo por arquivo e em modo por diretório, confirmando que cada item gera o consolidado correspondente no destino solicitado.

### Tests for User Story 1

- [ ] T011 [P] [US1] Add unit tests for request building, item resolution and per-item output derivation in /mnt/c/whatsweb/adapta-cli/tests/unit/test_destilador_service.py
- [ ] T012 [P] [US1] Add integration test for single-file `destilador` execution in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_command.py
- [ ] T013 [P] [US1] Add integration test for directory-mode `destilador` execution in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_directory_command.py
- [ ] T014 [P] [US1] Add integration test for explicit output file persistence in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_output_file.py

### Implementation for User Story 1

- [ ] T015 [US1] Implement file-mode and directory-mode request resolution in /mnt/c/whatsweb/adapta-cli/src/adapta/services/destilador_service.py
- [ ] T016 [US1] Implement internalized 7-dimension processing and final consolidation per item in /mnt/c/whatsweb/adapta-cli/src/adapta/services/destilador_service.py
- [ ] T017 [US1] Wire the `destilador` CLI command for `--input`, `--output`, `--input-dir` and `--output-dir` in /mnt/c/whatsweb/adapta-cli/src/adapta/cli.py
- [ ] T018 [US1] Implement terminal summaries and final save reporting for `destilador` in /mnt/c/whatsweb/adapta-cli/src/adapta/services/output_service.py

**Checkpoint**: User Story 1 should be fully functional and independently testable

---

## Phase 4: User Story 2 - Receber erros acionáveis para entradas inválidas (Priority: P2)

**Goal**: Rejeitar cedo combinações inválidas, origens inexistentes e destinos não graváveis com mensagens curtas e acionáveis.

**Independent Test**: Executar o comando com combinações inválidas de `--input`/`--output` e `--input-dir`/`--output-dir`, além de caminhos inexistentes, validando erros claros e retorno com código `1`.

### Tests for User Story 2

- [ ] T019 [P] [US2] Add unit tests for invalid parameter combinations and path validation in /mnt/c/whatsweb/adapta-cli/tests/unit/test_cli.py
- [ ] T020 [P] [US2] Add unit tests for service-side validation errors in /mnt/c/whatsweb/adapta-cli/tests/unit/test_destilador_service.py
- [ ] T021 [P] [US2] Add integration test for invalid input and output combinations in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_validation.py

### Implementation for User Story 2

- [ ] T022 [US2] Implement CLI validation for mutually exclusive and required parameter sets in /mnt/c/whatsweb/adapta-cli/src/adapta/cli.py
- [ ] T023 [US2] Implement early file and directory validation with friendly errors in /mnt/c/whatsweb/adapta-cli/src/adapta/services/destilador_service.py

**Checkpoint**: User Story 2 should be independently testable through failing command scenarios

---

## Phase 5: User Story 3 - Preservar o comportamento operacional do destilador existente (Priority: P3)

**Goal**: Manter retries por dimensão, limpeza best-effort e preservação de intermediários úteis em falhas ou interrupções, tudo internalizado no projeto.

**Independent Test**: Simular respostas inválidas, falhas parciais e interrupções controladas para verificar retries, preservação de artefatos e cleanup best-effort.

### Tests for User Story 3

- [ ] T024 [P] [US3] Add unit tests for dimension retries, best-result selection and preserved artifacts in /mnt/c/whatsweb/adapta-cli/tests/unit/test_destilador_service.py
- [ ] T025 [P] [US3] Add integration test for partial-failure handling and cleanup warnings in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_resilience.py

### Implementation for User Story 3

- [ ] T026 [US3] Implement retry loops, best-content selection and cleanup tracking in /mnt/c/whatsweb/adapta-cli/src/adapta/services/destilador_service.py
- [ ] T027 [US3] Implement best-effort local and remote cleanup plus preserved-artifact reporting in /mnt/c/whatsweb/adapta-cli/src/adapta/services/destilador_service.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validar os fluxos finais e fechar pendências transversais

- [ ] T028 [P] Validate quickstart examples for file mode and directory mode in /mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/quickstart.md
- [ ] T029 Run focused `destilador` test suites in /mnt/c/whatsweb/adapta-cli/tests/unit/test_cli.py, /mnt/c/whatsweb/adapta-cli/tests/unit/test_destilador_service.py, /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_command.py, /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_directory_command.py, /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_output_file.py, /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_validation.py, and /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_resilience.py
- [ ] T030 [P] Record new distillation-specific incidents in /mnt/c/whatsweb/adapta-cli/docs/licoes-aprendidas.md only if implementation reveals a new lesson
- [ ] T031 [P] Document and validate auxiliary file flows introduced after the base feature, including `list-files`, `--file` attachments and debate shared uploads in /mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/ and /mnt/c/whatsweb/adapta-cli/docs/

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - blocks all user stories
- **Phase 3 (US1)**: Depends on Phase 2 completion - establishes MVP for file and directory processing
- **Phase 4 (US2)**: Depends on Phase 2 completion and can build on the validated command surface from US1
- **Phase 5 (US3)**: Depends on Phase 2 completion and benefits from US1 pipeline implementation being available
- **Phase 6 (Polish)**: Depends on the desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 and has no dependency on other user stories
- **US2 (P2)**: Starts after Phase 2; reuses the same command interface but remains independently testable with invalid inputs
- **US3 (P3)**: Starts after Phase 2; extends the internalized pipeline behavior but remains independently testable through resilience scenarios

### Within Each User Story

- Tests MUST be written and fail before implementation
- Shared models and request resolution come before service orchestration
- Service implementation comes before CLI wiring and reporting
- Story-specific validation completes before moving to the next story

### Parallel Opportunities

- Phase 1 tasks `T002` to `T005` can run in parallel after `T001`
- Phase 2 tasks `T007` and `T008` can run in parallel after `T006`
- In US1, `T011`, `T012`, `T013`, and `T014` can run in parallel
- In US2, `T019`, `T020`, and `T021` can run in parallel
- In US3, `T024` and `T025` can run in parallel
- Phase 6 tasks `T028` and `T030` can run in parallel once implementation is stable

---

## Parallel Example: User Story 1

```bash
# Launch US1 tests together
Task: "Add unit tests for request building, item resolution and per-item output derivation in /mnt/c/whatsweb/adapta-cli/tests/unit/test_destilador_service.py"
Task: "Add integration test for single-file destilador execution in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_command.py"
Task: "Add integration test for directory-mode destilador execution in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_directory_command.py"
Task: "Add integration test for explicit output file persistence in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_output_file.py"
```

## Parallel Example: User Story 2

```bash
# Launch US2 validation tests together
Task: "Add unit tests for invalid parameter combinations and path validation in /mnt/c/whatsweb/adapta-cli/tests/unit/test_cli.py"
Task: "Add unit tests for service-side validation errors in /mnt/c/whatsweb/adapta-cli/tests/unit/test_destilador_service.py"
Task: "Add integration test for invalid input and output combinations in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_validation.py"
```

## Parallel Example: User Story 3

```bash
# Launch US3 resilience tests together
Task: "Add unit tests for dimension retries, best-result selection and preserved artifacts in /mnt/c/whatsweb/adapta-cli/tests/unit/test_destilador_service.py"
Task: "Add integration test for partial-failure handling and cleanup warnings in /mnt/c/whatsweb/adapta-cli/tests/integration/test_destilador_resilience.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate file mode and directory mode independently
5. Stop for review if only the MVP is needed

### Incremental Delivery

1. Setup + Foundational establish the internalized pipeline surface
2. Deliver US1 for file and directory processing
3. Deliver US2 for friendly validation failures
4. Deliver US3 for retries, cleanup and preserved-artifact behavior
5. Finish with quickstart validation and focused test runs

### Parallel Team Strategy

1. One developer updates `docs/` while another prepares the distillation service tests
2. After Foundation, one developer can own US1 while another prepares US2 validation coverage
3. US3 can begin once the base internalized pipeline from US1 is available behind failing resilience tests

---

## Notes

- All tasks follow the required checklist format with task ID and file path
- `[P]` tasks target different files or safe independent work
- Story labels appear only on user story tasks
- Documentation updates come before tests and implementation by constitution
- `docs/licoes-aprendidas.md` should only change if implementation reveals a genuinely new lesson
