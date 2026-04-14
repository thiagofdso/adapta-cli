# Implementation Plan: Persona Generator

**Branch**: `[001-build-adapta-cli]` | **Date**: 2026-04-14 | **Spec**: [/mnt/c/whatsweb/adapta-cli/specs/001-persona-generator/spec.md](/mnt/c/whatsweb/adapta-cli/specs/001-persona-generator/spec.md)
**Input**: Feature specification from `/specs/001-persona-generator/spec.md`

## Summary

Adicionar um comando de CLI interativo para coletar respostas de persona em 6 blocos, gerar um documento markdown usando o modelo Claude com prompt fixo e salvar o resultado em uma pasta de personas sob o diretório home do usuário, compatível com Linux e Windows, com confirmação antes de sobrescrever e limpeza da conversa remota ao final.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Typer, httpx, pydantic-settings, python-dotenv, pytest  
**Storage**: Arquivos markdown e JSON no diretório do usuário; conversa remota efêmera no serviço Adapta  
**Testing**: pytest com testes unitários e de integração da CLI  
**Target Platform**: CLI multiplataforma em Linux e Windows, com resolução correta do diretório home do usuário  
**Project Type**: CLI de processo único  
**Performance Goals**: Usuário deve conseguir concluir a entrevista curta em uma única execução interativa sem etapas extras de configuração ou seleção de modelo  
**Constraints**: nome e cargo obrigatórios; demais campos opcionais; nome validado logo na primeira pergunta; preservação de campos vazios no JSON enviado ao gerador; confirmação explícita antes de sobrescrever; resolução de caminho compatível com Linux e Windows; exclusão best-effort da conversa remota em sucesso e falha  
**Scale/Scope**: Um novo comando interativo, um novo serviço de geração de persona, persistência local de um arquivo por persona e cobertura de testes para fluxo obrigatório, sobrescrita e cleanup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Documentation-First Development**: PASS. O plano já considera atualização de `docs/features.md`, `docs/code-map.md`, `docs/arquitetura.md`, `docs/modelo-dados.md`, `docs/integracoes.md` e avaliação de `docs/licoes-aprendidas.md`.
- **Architecture Decisions Must Be Recorded**: PASS. O desenho reaproveita padrões existentes de comando Typer, serviço dedicado, registro de modelos e cleanup efêmero; não há nova decisão arquitetural transversal prevista neste escopo.
- **Documentation-First and Test-First Delivery**: PASS. A execução prevista segue documentação antes de testes e implementação, depois testes unitários antes do código e testes de integração para o comando.
- **Integration and Operational Validation**: PASS. O plano inclui validação explícita do fluxo remoto com modelo Claude, persistência local em `Path.home()` e cleanup da conversa remota ao final.
- **Simplicity, Consistency, and Learning**: PASS. A feature será implementada com o menor conjunto possível de novos componentes, seguindo padrões já existentes para comando, serviço, persistência de saída e mensagens de erro.

**Documentation Impact**:

- `docs/features.md`: adicionar a feature de geração de persona e o comportamento de salvamento/cleanup, incluindo a resolução do diretório home em Linux e Windows.
- `docs/code-map.md`: mapear novo comando e novo serviço.
- `docs/arquitetura.md`: incluir o novo fluxo CLI -> serviço -> cliente Adapta -> arquivo local.
- `docs/modelo-dados.md`: adicionar entidades de questionário de persona, documento e resultado.
- `docs/integracoes.md`: registrar o uso do chat efêmero para geração de persona.
- `docs/licoes-aprendidas.md`: atualizar apenas se surgir incidente ou erro relevante durante a implementação.
- `docs/adr/`: nenhum ADR novo planejado nesta fase.

## Project Structure

### Documentation (this feature)

```text
specs/001-persona-generator/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── persona-command.md
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
    ├── registry.py
    └── services/
        ├── chat_service.py
        ├── output_service.py
        ├── prompt_service.py
        └── persona_service.py

tests/
├── integration/
│   └── test_persona_command.py
└── unit/
    ├── test_cli.py
    └── test_persona_service.py
```

**Structure Decision**: Manter a estrutura única existente em `src/adapta/`, adicionando um comando novo em `src/adapta/cli.py`, um serviço dedicado em `src/adapta/services/persona_service.py` e testes unitários/integrados específicos, sem criar novas camadas ou pacotes.

## Phase 0 Research Summary

- Reutilizar `typer.prompt` e loops pequenos no comando para entrevista e revalidação imediata do nome.
- Reutilizar o padrão de escrita via helper de saída e resolver o diretório base com a API de diretório home compatível com Linux e Windows.
- Fixar o modelo lógico em `claude` via `registry`, sem `--model`, sem seleção interativa e sem depender de `ADAPTA_MODEL`.
- Preferir fluxo remoto efêmero com cleanup garantido em `finally`, preservando sucesso local mesmo se a limpeza falhar.

## Phase 1 Design Summary

- Definir um modelo de dados funcional com questionário, pedido de geração, documento final e resultado da execução.
- Formalizar o contrato do comando `persona` cobrindo prompts, validações, confirmação de sobrescrita e saída de sucesso/erro.
- Registrar um quickstart de implementação seguindo documentação primeiro, TDD e validação operacional, incluindo cobertura para resolução do diretório home em Linux e Windows.

## Post-Design Constitution Check

- **Documentation-First Development**: PASS. Todos os documentos obrigatórios impactados foram mapeados no plano e nos artefatos de design.
- **Architecture Decisions Must Be Recorded**: PASS. O desenho continua dentro dos padrões arquiteturais já registrados; nenhum trade-off novo exige ADR nesta fase.
- **Documentation-First and Test-First Delivery**: PASS. O quickstart e o contrato definem ordem doc-first e TDD explícita.
- **Integration and Operational Validation**: PASS. O contrato e o quickstart cobrem cleanup remoto, confirmação de sobrescrita e persistência local sob `home`.
- **Simplicity, Consistency, and Learning**: PASS. O design mantém um único comando, um único serviço novo e reaproveita mecanismos existentes.

## Complexity Tracking

Nenhuma violação da constituição identificada nesta fase.
