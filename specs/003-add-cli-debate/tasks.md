# Tasks: Debate no CLI

**Input**: Design documents from `/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/`
**Prerequisites**: `/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/plan.md`, `/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/spec.md`, `/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/research.md`, `/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/data-model.md`, `/mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/contracts/debate-command.md`

**Tests**: TDD obrigatório por constituição do repositório. Cada história inclui tarefas de testes antes da implementação.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- All task descriptions include exact file paths

## Phase 1: Setup (Shared Documentation)

**Purpose**: Atualizar a documentação obrigatória em `docs/` antes de testes e implementação

- [X] T001 Update feature catalog for `debate` in /mnt/c/whatsweb/adapta-cli/docs/features.md
- [X] T002 [P] Update command map for `debate` flow in /mnt/c/whatsweb/adapta-cli/docs/code-map.md
- [X] T003 [P] Update multi-agent CLI architecture notes in /mnt/c/whatsweb/adapta-cli/docs/arquitetura.md
- [X] T004 [P] Add debate entities and relationships in /mnt/c/whatsweb/adapta-cli/docs/modelo-dados.md
- [X] T005 [P] Document multi-chat Adapta integration and cleanup expectations in /mnt/c/whatsweb/adapta-cli/docs/integracoes.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared structures and command scaffolding required before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Add debate dataclasses and result artifacts in /mnt/c/whatsweb/adapta-cli/src/adapta/models.py
- [X] T007 [P] Extend transcript persistence helpers for debate artifacts in /mnt/c/whatsweb/adapta-cli/src/adapta/services/output_service.py
- [X] T008 [P] Add multi-session cleanup helpers for debate chats in /mnt/c/whatsweb/adapta-cli/src/adapta/services/chat_service.py
- [X] T009 Create debate service scaffold with shared validation entrypoints in /mnt/c/whatsweb/adapta-cli/src/adapta/services/debate_service.py
- [X] T010 Register the `debate` command skeleton and shared option parsing in /mnt/c/whatsweb/adapta-cli/src/adapta/cli.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Executar debate configurado por arquivo (Priority: P1) 🎯 MVP

**Goal**: Permitir debates completos a partir de arquivo de configuração ou caminho explícito, com rodadas, conclusão final e gravação opcional em arquivo.

**Independent Test**: Executar `adapta debate` com `--config`, `--prompt` e `--rounds`, confirmando respostas por rodada, conclusão final e artefato salvo quando `--output` for usado.

### Tests for User Story 1

- [X] T011 [P] [US1] Add unit tests for config-file parsing, model resolution and round orchestration in /mnt/c/whatsweb/adapta-cli/tests/unit/test_debate_service.py
- [X] T012 [P] [US1] Add integration test for configured debate execution in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_command.py
- [X] T013 [P] [US1] Add integration test for saved debate artifact output in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_output_file.py

### Implementation for User Story 1

- [X] T014 [US1] Implement config-file loading, per-agent session setup and round execution in /mnt/c/whatsweb/adapta-cli/src/adapta/services/debate_service.py
- [X] T015 [US1] Implement configured `debate` command flow with `--config`, `--prompt`, `--rounds` and default `--model-conclusion` in /mnt/c/whatsweb/adapta-cli/src/adapta/cli.py
- [X] T016 [US1] Implement final transcript rendering and optional file persistence for debate results in /mnt/c/whatsweb/adapta-cli/src/adapta/services/output_service.py

**Checkpoint**: User Story 1 should be fully functional and independently testable

---

## Phase 4: User Story 2 - Montar debate interativamente sem arquivo prévio (Priority: P2)

**Goal**: Guiar o usuário por perguntas interativas quando não houver `--config` nem `ADAPTA_DEBATE_CONFIG`, salvando `debate.json` ao final.

**Independent Test**: Executar `adapta debate` sem `--config`, sem `ADAPTA_DEBATE_CONFIG` e sem `--rounds`, responder às perguntas e verificar a criação de `debate.json` com uma configuração válida.

### Tests for User Story 2

- [X] T017 [P] [US2] Add unit tests for interactive numeric validation and config persistence in /mnt/c/whatsweb/adapta-cli/tests/unit/test_cli.py
- [X] T018 [P] [US2] Add integration test for interactive debate setup and `debate.json` creation in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_interactive.py

### Implementation for User Story 2

- [X] T019 [US2] Implement interactive prompts for agent count, agent models, agent prompts and rounds in /mnt/c/whatsweb/adapta-cli/src/adapta/cli.py
- [X] T020 [US2] Implement `ADAPTA_DEBATE_CONFIG` fallback resolution and `debate.json` persistence in /mnt/c/whatsweb/adapta-cli/src/adapta/services/debate_service.py

**Checkpoint**: User Story 2 should work independently from a fresh terminal session

---

## Phase 5: User Story 3 - Acompanhar o debate em tempo real no terminal (Priority: P3)

**Goal**: Exibir cada resposta concluída no terminal sem `--output`, com identificação clara de agente e rodada.

**Independent Test**: Executar um debate sem `--output` e confirmar que cada bloco é impresso assim que chega, com cabeçalhos equivalentes a `Agente 1 Rodada 1`.

### Tests for User Story 3

- [X] T021 [P] [US3] Add unit tests for turn labels and no-output emission callbacks in /mnt/c/whatsweb/adapta-cli/tests/unit/test_debate_service.py
- [X] T022 [P] [US3] Add integration test for live terminal output without `--output` in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_streaming.py

### Implementation for User Story 3

- [X] T023 [US3] Implement per-turn emission and `Agente N Rodada N` labeling in /mnt/c/whatsweb/adapta-cli/src/adapta/services/debate_service.py
- [X] T024 [US3] Wire live terminal printing for no-output debate runs in /mnt/c/whatsweb/adapta-cli/src/adapta/cli.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validar o fluxo completo e fechar pendências transversais

- [X] T025 [P] Validate the examples and expected outcomes in /mnt/c/whatsweb/adapta-cli/specs/003-add-cli-debate/quickstart.md
- [X] T026 Run focused debate test suites in /mnt/c/whatsweb/adapta-cli/tests/unit/test_cli.py, /mnt/c/whatsweb/adapta-cli/tests/unit/test_debate_service.py, /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_command.py, /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_output_file.py, /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_interactive.py, and /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_streaming.py
- [X] T027 [P] Record any debate-specific debugging lessons or operational incidents in /mnt/c/whatsweb/adapta-cli/docs/licoes-aprendidas.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - blocks all user stories
- **Phase 3 (US1)**: Depends on Phase 2 completion - establishes MVP
- **Phase 4 (US2)**: Depends on Phase 2 completion and can proceed after US1 if sharing the same command flow changes needs to be merged safely
- **Phase 5 (US3)**: Depends on Phase 2 completion and benefits from US1 debate execution being available
- **Phase 6 (Polish)**: Depends on the user stories selected for delivery

### User Story Dependencies

- **US1 (P1)**: Starts after Phase 2 and has no dependency on other user stories
- **US2 (P2)**: Starts after Phase 2; reuses the same `debate` command entrypoint but remains independently testable
- **US3 (P3)**: Starts after Phase 2; reuses debate execution from US1 but remains independently testable through no-output runs

### Within Each User Story

- Tests MUST be written and fail before implementation
- Shared data structures and service hooks come before command wiring
- Service implementation comes before terminal and file output integration
- Story-specific validation completes before moving to the next story

### Parallel Opportunities

- Phase 1 documentation tasks marked `[P]` can run in parallel after `T001`
- Phase 2 tasks `T007` and `T008` can run in parallel after `T006`
- In US1, `T011`, `T012`, and `T013` can run in parallel
- In US2, `T017` and `T018` can run in parallel
- In US3, `T021` and `T022` can run in parallel
- Phase 6 tasks `T025` and `T027` can run in parallel once the targeted stories are complete

---

## Parallel Example: User Story 1

```bash
# Launch US1 tests together
Task: "Add unit tests for config-file parsing, model resolution and round orchestration in /mnt/c/whatsweb/adapta-cli/tests/unit/test_debate_service.py"
Task: "Add integration test for configured debate execution in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_command.py"
Task: "Add integration test for saved debate artifact output in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_output_file.py"
```

## Parallel Example: User Story 2

```bash
# Launch US2 tests together
Task: "Add unit tests for interactive numeric validation and config persistence in /mnt/c/whatsweb/adapta-cli/tests/unit/test_cli.py"
Task: "Add integration test for interactive debate setup and debate.json creation in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_interactive.py"
```

## Parallel Example: User Story 3

```bash
# Launch US3 tests together
Task: "Add unit tests for turn labels and no-output emission callbacks in /mnt/c/whatsweb/adapta-cli/tests/unit/test_debate_service.py"
Task: "Add integration test for live terminal output without --output in /mnt/c/whatsweb/adapta-cli/tests/integration/test_debate_streaming.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Validate configured debate execution and saved artifact paths
5. Stop for review if only MVP is needed

### Incremental Delivery

1. Setup + Foundational establish the shared debate command surface
2. Deliver US1 for configured debates and final conclusion generation
3. Deliver US2 for interactive setup and `debate.json` reuse
4. Deliver US3 for live terminal visibility without `--output`
5. Finish with quickstart validation, focused test runs and operational notes

### Parallel Team Strategy

1. One developer updates `docs/` while another prepares Phase 2 design details
2. After Foundation, one developer can own US1 while another prepares US2 tests
3. US3 can start once the debate execution path from US1 is merged or stubbed behind failing tests

---

## Notes

- All tasks follow the required checklist format with task ID and file path
- `[P]` tasks target different files or safe independent work
- Story labels appear only on user story tasks
- Documentation updates are intentionally placed before tests and implementation
- `docs/licoes-aprendidas.md` should only receive concrete lessons discovered during implementation
