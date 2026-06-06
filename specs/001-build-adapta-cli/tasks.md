# Tasks: Build Adapta CLI

**Input**: Design documents from `/specs/001-build-adapta-cli/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-contract.md, quickstart.md

**Tests**: TDD obrigatório. Testes unitários devem ser escritos e executados antes da implementação; testes de integração entram apenas após a suíte unitária estar verde.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project layout at repository root
- Source code in `src/adapta/`
- Tests in `tests/unit/` and `tests/integration/`
- Installer scripts in `scripts/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicializar o projeto Python empacotado, estrutura base e atalhos de desenvolvimento.

- [x] T001 Create mandatory project documentation structure in `docs/`, including `docs/adr/`
- [x] T002 [P] Create initial business feature map in `docs/features.md` and documentation usage guide in `docs/guia-uso-documentacao.md`
- [x] T003 [P] Create initial technical documentation in `docs/code-map.md`, `docs/arquitetura.md`, `docs/modelo-dados.md`, `docs/integracoes.md`, and `docs/licoes-aprendidas.md`
- [x] T004 Create Python package layout and test directories in `src/adapta/`, `src/adapta/services/`, `tests/unit/`, and `tests/integration/`
- [x] T005 Create project metadata and console entry point in `pyproject.toml`
- [x] T006 [P] Create package bootstrap files in `src/adapta/__init__.py`, `src/adapta/__main__.py`, and `src/adapta/services/__init__.py`
- [x] T007 [P] Copy authentication environment file from `/mnt/c/whatsweb/adapta/.env` to `/mnt/c/whatsweb/adapta-cli/.env`
- [x] T008 Create development shortcuts in `Makefile` for `test`, `prompt`, and `chat`
- [x] T009 [P] Create local installer script in `scripts/install-local.sh`
- [x] T010 [P] Create remote installer script in `scripts/install-remote.sh`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implementar a infraestrutura central compartilhada por todas as histórias.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T011 Create typed settings loader for `.env` and default model resolution in `src/adapta/config.py`
- [x] T012 [P] Create model registry and model option mappings in `src/adapta/registry.py`
- [x] T013 [P] Create execution and domain dataclasses in `src/adapta/models.py`
- [x] T014 [P] Create opt-in log configuration helpers with default silent behavior in `src/adapta/logging.py`
- [x] T015 Create async runtime helpers for sync CLI entrypoints in `src/adapta/runtime.py`
- [x] T016 Create Adapta client adapter and shared async lifecycle wrapper in `src/adapta/client.py`
- [x] T017 [P] Create output persistence helper for stdout and file writes in `src/adapta/services/output_service.py`
- [x] T018 Create top-level Typer app, global log options, and command wiring shell in `src/adapta/cli.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Executar um prompt único pelo terminal (Priority: P1) 🎯 MVP

**Goal**: Permitir prompt inline ou por arquivo, retorno em terminal e gravação opcional em arquivo.

**Independent Test**: Executar `adapta prompt` com `--prompt` ou `--prompt-file`, com e sem `--output`, validando resposta, leitura correta da entrada e escrita opcional do arquivo.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T019 [P] [US1] Update prompt feature and flow documentation in `docs/features.md`, `docs/code-map.md`, and `docs/integracoes.md`
- [x] T020 [P] [US1] Create unit tests for prompt input validation and prompt-source exclusivity in `tests/unit/test_cli.py`
- [x] T021 [P] [US1] Create unit tests for prompt request parsing and file loading in `tests/unit/test_prompt_service.py`
- [x] T022 [P] [US1] Create unit tests for stdout and output file persistence in `tests/unit/test_prompt_service.py`
- [x] T023 [P] [US1] Create unit tests for default no-log behavior and `--log info` or `--log debug` on prompt command in `tests/unit/test_logging.py`
- [x] T024 [US1] Run failing unit tests for User Story 1 with `pytest tests/unit/test_cli.py tests/unit/test_prompt_service.py tests/unit/test_logging.py`

### Implementation for User Story 1

- [x] T025 [P] [US1] Implement prompt request assembly and prompt-file reading in `src/adapta/services/prompt_service.py`
- [x] T026 [US1] Implement prompt command flow and argument validation in `src/adapta/cli.py`
- [x] T027 [US1] Implement prompt execution against the shared client adapter in `src/adapta/services/prompt_service.py`
- [x] T028 [US1] Integrate output persistence for prompt responses in `src/adapta/services/output_service.py` and `src/adapta/cli.py`
- [x] T029 [US1] Integrate runtime and opt-in logging configuration for prompt execution in `src/adapta/runtime.py`, `src/adapta/logging.py`, and `src/adapta/cli.py`
- [x] T030 [US1] Run unit test suite for User Story 1 with `pytest tests/unit/test_cli.py tests/unit/test_prompt_service.py tests/unit/test_logging.py`
- [x] T031 [P] [US1] Create integration test for inline prompt response in `tests/integration/test_prompt_command.py`
- [x] T032 [P] [US1] Create integration test for prompt file input and output file writing in `tests/integration/test_prompt_file_command.py` and `tests/integration/test_output_file_command.py`
- [x] T033 [US1] Run integration tests for User Story 1 with `pytest tests/integration/test_prompt_command.py tests/integration/test_prompt_file_command.py tests/integration/test_output_file_command.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Conversar em modo chat (Priority: P2)

**Goal**: Iniciar chat interativo com histórico local, respostas contextuais e limpeza do chat remoto ao encerrar.

**Independent Test**: Executar `adapta chat --model ...`, trocar múltiplas mensagens na mesma sessão e confirmar tentativa de exclusão do chat remoto ao sair.

### Tests for User Story 2 ⚠️

- [x] T034 [P] [US2] Update chat flow documentation in `docs/features.md`, `docs/code-map.md`, `docs/modelo-dados.md`, and `docs/integracoes.md`
- [x] T035 [P] [US2] Create unit tests for chat session lifecycle and message accumulation in `tests/unit/test_chat_service.py`
- [x] T036 [P] [US2] Create unit tests for chat command loop, exit flow, and cleanup warnings in `tests/unit/test_cli.py`
- [x] T037 [P] [US2] Create unit tests for chat cleanup and client finalization behavior in `tests/unit/test_chat_service.py`
- [x] T038 [US2] Run failing unit tests for User Story 2 with `pytest tests/unit/test_chat_service.py tests/unit/test_cli.py`

### Implementation for User Story 2

- [x] T039 [P] [US2] Implement chat session state and message orchestration in `src/adapta/services/chat_service.py`
- [x] T040 [US2] Implement chat command interactive loop and exit handling in `src/adapta/cli.py`
- [x] T041 [US2] Implement remote chat deletion and cleanup warnings in `src/adapta/services/chat_service.py` and `src/adapta/client.py`
- [x] T042 [US2] Integrate runtime lifecycle for chat command in `src/adapta/runtime.py` and `src/adapta/cli.py`
- [x] T043 [US2] Run unit test suite for User Story 2 with `pytest tests/unit/test_chat_service.py tests/unit/test_cli.py`
- [x] T044 [P] [US2] Create integration test for chat cleanup on session end in `tests/integration/test_chat_cleanup.py`
- [x] T045 [US2] Run integration tests for User Story 2 with `pytest tests/integration/test_chat_cleanup.py`

**Checkpoint**: At this point, User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Selecionar um modelo padrão ou interativo (Priority: P3)

**Goal**: Resolver modelo por parâmetro, `ADAPTA_MODEL` ou seleção interativa antes de prompt e chat.

**Independent Test**: Executar prompt e chat sem `--model`, validando uso do padrão do ambiente ou a seleção interativa quando não houver padrão configurado.

### Tests for User Story 3 ⚠️

- [x] T046 [P] [US3] Update model selection documentation in `docs/features.md`, `docs/code-map.md`, and `docs/modelo-dados.md`
- [x] T047 [P] [US3] Create unit tests for settings loading and `ADAPTA_MODEL` fallback in `tests/unit/test_config.py`
- [x] T048 [P] [US3] Create unit tests for model registry aliases and selection prompts in `tests/unit/test_registry.py`
- [x] T049 [P] [US3] Create unit tests for prompt and chat model resolution flows in `tests/unit/test_cli.py`
- [x] T050 [US3] Run failing unit tests for User Story 3 with `pytest tests/unit/test_config.py tests/unit/test_registry.py tests/unit/test_cli.py`

### Implementation for User Story 3

- [x] T051 [P] [US3] Implement default-model validation and environment loading rules in `src/adapta/config.py`
- [x] T052 [P] [US3] Implement model alias registry and interactive selection helpers in `src/adapta/registry.py`
- [x] T053 [US3] Integrate shared model resolution into prompt and chat commands in `src/adapta/cli.py`
- [x] T054 [US3] Run unit test suite for User Story 3 with `pytest tests/unit/test_config.py tests/unit/test_registry.py tests/unit/test_cli.py`
- [x] T055 [P] [US3] Create integration test for default model resolution and interactive fallback in `tests/integration/test_prompt_command.py` and `tests/integration/test_chat_cleanup.py`
- [x] T056 [US3] Run integration tests for User Story 3 with `pytest tests/integration/test_prompt_command.py tests/integration/test_chat_cleanup.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Fechar instalação, atalhos operacionais, documentação e validação final do fluxo completo.

- [x] T057 [P] Update installation and development workflow docs in `docs/features.md`, `docs/code-map.md`, `docs/arquitetura.md`, and `docs/guia-uso-documentacao.md`
- [x] T058 [P] Create ADR for architectural packaging or installation decision in `docs/adr/ADR-001-cli-packaging.md` if needed
- [x] T059 [P] Create unit tests for installer scripts behavior in `tests/unit/test_install_scripts.py`
- [x] T060 [P] Create unit tests for `Makefile` targets and forwarded arguments in `tests/unit/test_makefile.py`
- [x] T061 Create implementation for installer scripts in `scripts/install-local.sh` and `scripts/install-remote.sh`
- [x] T062 Create implementation for `Makefile` targets in `Makefile`
- [x] T063 Create integration test for local and remote installation flow in `tests/integration/test_installation_flow.py`
- [x] T064 Run remaining unit test suite with `pytest tests/unit`
- [x] T065 Run remaining integration suite with `pytest tests/integration`
- [x] T066 Record relevant implementation mistakes or incidents in `docs/licoes-aprendidas.md`
- [x] T067 Validate quickstart scenarios and update usage notes in `specs/001-build-adapta-cli/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion and can begin after Phase 3 starts if capacity allows
- **User Story 3 (Phase 5)**: Depends on Foundational completion and can begin after Phase 3 starts if capacity allows
- **Polish (Phase 6)**: Depends on desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - MVP baseline for prompt execution
- **User Story 2 (P2)**: Depends on foundational client/runtime pieces; functionally independent from US1 once shared infrastructure exists
- **User Story 3 (P3)**: Depends on foundational config/registry pieces; integrates with both prompt and chat but remains independently testable

### Within Each User Story

- Unit tests MUST be written and fail before implementation
- Implementation follows tests, then green unit suite
- Integration tests are written only after unit tests pass for that story
- Story-specific integration tests run before moving to the next checkpoint

### Parallel Opportunities

- T002 and T003 can run in parallel after T001
- T006, T007, T009, and T010 can run in parallel after T005
- T012, T013, T014, and T017 can run in parallel after T011
- US1 documentation and test creation tasks T019-T023 can run in parallel where files do not overlap
- US1 integration test creation tasks T031 and T032 can run in parallel
- US2 documentation and test creation tasks T034-T037 can run in parallel where files do not overlap
- US3 documentation and test creation tasks T046-T049 can run in parallel where files do not overlap
- Polish tasks T057-T060 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Update docs and write User Story 1 tests together
Task: "Update prompt feature and flow documentation in docs/features.md, docs/code-map.md, and docs/integracoes.md"
Task: "Create unit tests for prompt input validation and prompt-source exclusivity in tests/unit/test_cli.py"
Task: "Create unit tests for prompt request parsing and file loading in tests/unit/test_prompt_service.py"
Task: "Create unit tests for stdout and output file persistence in tests/unit/test_prompt_service.py"
Task: "Create unit tests for default no-log behavior and --log info or --log debug on prompt command in tests/unit/test_logging.py"

# After unit tests are green, write integration coverage together
Task: "Create integration test for inline prompt response in tests/integration/test_prompt_command.py"
Task: "Create integration test for prompt file input and output file writing in tests/integration/test_prompt_file_command.py and tests/integration/test_output_file_command.py"
```

---

## Parallel Example: User Story 2

```bash
Task: "Update chat flow documentation in docs/features.md, docs/code-map.md, docs/modelo-dados.md, and docs/integracoes.md"
Task: "Create unit tests for chat session lifecycle and message accumulation in tests/unit/test_chat_service.py"
Task: "Create unit tests for chat command loop, exit flow, and cleanup warnings in tests/unit/test_cli.py"
Task: "Create unit tests for chat cleanup and client finalization behavior in tests/unit/test_chat_service.py"
```

---

## Parallel Example: User Story 3

```bash
Task: "Update model selection documentation in docs/features.md, docs/code-map.md, and docs/modelo-dados.md"
Task: "Create unit tests for settings loading and ADAPTA_MODEL fallback in tests/unit/test_config.py"
Task: "Create unit tests for model registry aliases and selection prompts in tests/unit/test_registry.py"
Task: "Create unit tests for prompt and chat model resolution flows in tests/unit/test_cli.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 using documentation updates before tests and code
4. **STOP and VALIDATE** with the prompt flows and output file behavior
5. Demo `adapta prompt`, `make prompt`, and prompt-file execution

### Incremental Delivery

1. Complete Setup + Foundational
2. Deliver User Story 1 and validate prompt flows
3. Deliver User Story 2 and validate chat cleanup
4. Deliver User Story 3 and validate default/interative model selection
5. Finish installers, `Makefile`, and full regression pass

### Parallel Team Strategy

1. One developer completes Setup + Foundational
2. After foundation is ready:
3. Developer A: US1 prompt flow
4. Developer B: US2 chat flow
5. Developer C: US3 model resolution flow
6. Final shared pass covers installers, `Makefile`, and full-suite validation

---

## Notes

- [P] tasks touch different files and can be split safely
- User story labels map each task to a specific independently testable increment
- Documentation must be updated before tests and implementation for each impacted flow
- Integration tests must not be started before the corresponding unit tests are green
- Installation and `Makefile` work are kept in the final phase because they span multiple stories and packaging concerns
