# Tasks: Persona Generator

**Input**: Design documents from `/specs/001-persona-generator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/persona-command.md, quickstart.md

**Tests**: Testes unitários e de integração são obrigatórios para esta feature conforme plan.md, contract e quickstart.

**Organization**: Tasks agrupadas por história de usuário para permitir implementação e teste independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: História de usuário associada (`[US1]`, `[US2]`, `[US3]`)
- Todas as tasks incluem caminho exato de arquivo

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar documentação, contratos de teste e arquivos-base da feature

- [x] T001 Atualizar `specs/001-persona-generator/tasks.md` com o plano executável final
- [x] T002 [P] Atualizar `docs/features.md` com a feature de geração de persona
- [x] T003 [P] Atualizar `docs/code-map.md` com o comando `persona` e o serviço correspondente
- [x] T004 [P] Atualizar `docs/arquitetura.md` com o fluxo CLI -> serviço -> cliente -> arquivo local
- [x] T005 [P] Atualizar `docs/modelo-dados.md` com entidades e estados da geração de persona
- [x] T006 [P] Atualizar `docs/integracoes.md` com a integração de conversa efêmera para persona

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Criar a base compartilhada que bloqueia todas as histórias

**⚠️ CRITICAL**: Nenhuma história pode avançar antes desta fase

- [x] T007 [P] Criar o arquivo `src/adapta/services/persona_service.py` com modelos e helpers base do fluxo de persona
- [x] T008 [P] Criar `tests/unit/test_persona_service.py` com testes vermelhos para normalização do nome, payload JSON e resolução multiplataforma do diretório home
- [x] T009 [P] Estender `tests/unit/test_cli.py` com testes vermelhos para prompts obrigatórios e re-prompt do nome no comando `src/adapta/cli.py`
- [x] T010 Implementar em `src/adapta/services/persona_service.py` a estrutura base de questionário, slug seguro, caminho de saída e payload para Claude
- [x] T011 Implementar em `src/adapta/cli.py` o esqueleto do comando `persona` com blocos de perguntas e sem seleção manual de modelo

**Checkpoint**: Base pronta para implementar as histórias

---

## Phase 3: User Story 1 - Gerar persona guiada (Priority: P1) 🎯 MVP

**Goal**: Entregar o fluxo interativo mínimo que coleta respostas, gera a persona com Claude e salva o markdown no home do usuário

**Independent Test**: Executar `adapta persona`, informar nome e cargo, deixar o restante vazio e verificar que um markdown válido é salvo no diretório de personas do home do usuário sem inventar campos.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T012 [P] [US1] Adicionar cenários unitários em `tests/unit/test_persona_service.py` para questionário mínimo, validação de cargo obrigatório e montagem do prompt com campos vazios preservados
- [x] T013 [P] [US1] Adicionar cenários unitários em `tests/unit/test_cli.py` para entrevista em 6 blocos, re-prompt do nome inválido e bloqueio de cargo vazio
- [x] T014 [P] [US1] Criar `tests/integration/test_persona_command.py` com fluxo mínimo de geração e salvamento em diretório home resolvido corretamente

### Implementation for User Story 1

- [x] T015 [US1] Implementar em `src/adapta/services/persona_service.py` a validação de `nome` e `cargo` e a serialização completa do `PersonaQuestionnaire`
- [x] T016 [US1] Implementar em `src/adapta/services/persona_service.py` a resolução do modelo `claude`, construção do prompt-base e geração do markdown final
- [x] T017 [US1] Implementar em `src/adapta/services/persona_service.py` a resolução multiplataforma do caminho lógico `~/.adapta/persona/{nome-persona}.md` e criação do diretório de destino
- [x] T018 [US1] Implementar em `src/adapta/cli.py` o fluxo completo de perguntas, incluindo títulos de blocos, prompts opcionais e delegação ao serviço de persona
- [x] T019 [US1] Integrar em `src/adapta/cli.py` a mensagem de sucesso com o caminho salvo e erros amigáveis sem traceback para o comando `persona`

**Checkpoint**: User Story 1 funcional e testável de forma independente

---

## Phase 4: User Story 2 - Proteger arquivo existente (Priority: P2)

**Goal**: Garantir confirmação explícita antes de sobrescrever persona existente e preservar o arquivo anterior quando o usuário recusar

**Independent Test**: Criar previamente um arquivo de persona com o mesmo nome, executar `adapta persona` e verificar que a recusa não altera o arquivo e a confirmação permite a substituição.

### Tests for User Story 2 ⚠️

- [x] T020 [P] [US2] Adicionar cenários unitários em `tests/unit/test_persona_service.py` para detecção de arquivo existente e decisão de sobrescrita
- [x] T021 [P] [US2] Estender `tests/unit/test_cli.py` com cenários de confirmação positiva e negativa de sobrescrita
- [x] T022 [P] [US2] Estender `tests/integration/test_persona_command.py` com fluxo de recusa e confirmação de sobrescrita

### Implementation for User Story 2

- [x] T023 [US2] Implementar em `src/adapta/services/persona_service.py` a verificação do destino existente e o bloqueio de gravação quando a sobrescrita for recusada
- [x] T024 [US2] Implementar em `src/adapta/cli.py` a confirmação explícita de sobrescrita antes de salvar o arquivo final
- [x] T025 [US2] Ajustar em `src/adapta/services/persona_service.py` o fluxo de persistência para substituir o arquivo somente após confirmação afirmativa

**Checkpoint**: User Stories 1 e 2 funcionam independentemente

---

## Phase 5: User Story 3 - Encerrar sessão sem resíduos (Priority: P3)

**Goal**: Garantir tentativa de exclusão da conversa temporária ao final, sem perder o resultado salvo em caso de falha no cleanup

**Independent Test**: Executar o fluxo com sucesso e com falha simulada no cleanup e verificar que a tentativa de exclusão sempre ocorre e que um warning não invalida o arquivo salvo.

### Tests for User Story 3 ⚠️

- [x] T026 [P] [US3] Adicionar cenários unitários em `tests/unit/test_persona_service.py` para cleanup em sucesso e warning de cleanup sem invalidar salvamento
- [x] T027 [P] [US3] Estender `tests/unit/test_cli.py` com cenário de aviso ao usuário quando o cleanup remoto falhar
- [x] T028 [P] [US3] Estender `tests/integration/test_persona_command.py` com cenário de tentativa de cleanup ao final da execução

### Implementation for User Story 3

- [x] T029 [US3] Implementar em `src/adapta/services/persona_service.py` o fluxo remoto efêmero com cleanup best-effort em `finally`
- [x] T030 [US3] Ajustar em `src/adapta/cli.py` a exibição de warning de cleanup remoto sem converter sucesso em falha

**Checkpoint**: Todas as histórias funcionam independentemente

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Fechamento, validação ampla e documentação final

- [x] T031 [P] Executar e ajustar `tests/unit/test_cli.py` e `tests/unit/test_persona_service.py`
- [x] T032 [P] Executar e ajustar `tests/integration/test_persona_command.py`
- [x] T033 [P] Executar a suíte completa `pytest` e corrigir regressões relacionadas
- [x] T034 Validar `specs/001-persona-generator/quickstart.md` contra a implementação final
- [x] T035 Atualizar `docs/licoes-aprendidas.md` se surgir incidente relevante durante a implementação

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências, começa imediatamente
- **Foundational (Phase 2)**: depende da conclusão do Setup e bloqueia todas as histórias
- **User Stories (Phases 3-5)**: dependem da conclusão da base; depois seguem em ordem P1 -> P2 -> P3
- **Polish (Phase 6)**: depende das histórias desejadas concluídas

### User Story Dependencies

- **US1**: começa após a fase Foundational, sem depender das demais
- **US2**: depende de US1 porque reaproveita o mesmo fluxo de geração e persistência
- **US3**: depende de US1 porque reaproveita o mesmo fluxo remoto e complementa o encerramento

### Within Each User Story

- Testes primeiro e em estado vermelho
- Serviço antes de integração final na CLI
- Implementação principal antes dos ajustes finais de UX
- Cada história precisa fechar seu teste independente antes de avançar

### Parallel Opportunities

- T002-T006 podem rodar em paralelo
- T007-T009 podem rodar em paralelo
- Em cada história, tasks de teste marcadas com `[P]` podem rodar em paralelo
- As tasks T031-T033 podem rodar em paralelo como validação final, se houver capacidade

---

## Parallel Example: User Story 1

```bash
# Testes vermelhos de US1 em paralelo
Task: "Adicionar cenários unitários em tests/unit/test_persona_service.py"
Task: "Adicionar cenários unitários em tests/unit/test_cli.py"
Task: "Criar tests/integration/test_persona_command.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Concluir Setup
2. Concluir Foundational
3. Concluir US1
4. Validar o fluxo mínimo de geração

### Incremental Delivery

1. Base pronta
2. Entregar US1 como MVP
3. Adicionar proteção de sobrescrita em US2
4. Adicionar cleanup robusto em US3
5. Finalizar com testes e documentação

### Parallel Team Strategy

1. Uma pessoa fecha Setup e Foundational
2. Depois:
   - Pessoa A avança US1
   - Pessoa B prepara testes de US2
   - Pessoa C prepara testes de US3

---

## Notes

- Todas as tasks seguem o formato obrigatório de checklist
- Cada história mantém critério de teste independente
- Atualizações em `docs/` fazem parte da entrega, não são opcionais
- Marcar tasks como concluídas em tempo real durante a implementação
