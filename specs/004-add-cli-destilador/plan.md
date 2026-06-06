# Implementation Plan: Destilador no CLI

**Branch**: `[001-build-adapta-cli]` | **Date**: 2026-04-12 | **Spec**: [`/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/spec.md`]  
**Input**: Feature specification from `/mnt/c/whatsweb/adapta-cli/specs/004-add-cli-destilador/spec.md`

## Summary

Adicionar um comando `destilador` ao CLI para processar tanto um arquivo individual quanto um diretório de entrada, produzindo arquivos consolidados em um caminho de saída explícito por arquivo ou por diretório. A lógica necessária do fluxo de destilação em 7 dimensões será internalizada no `adapta-cli`, sem depender de código-fonte externo em runtime. O desenho segue o padrão atual de comandos finos com serviço dedicado, validação explícita de arquivos e diretórios, listagem remota para deduplicação de uploads, persistência controlada e limpeza operacional best-effort para artefatos locais e remotos.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Typer, httpx, pydantic-settings, python-dotenv, pytest  
**Storage**: arquivos locais PDF e outros anexos suportados, arquivos texto/markdown de saída, diretórios temporários locais e artefatos remotos efêmeros no serviço Adapta  
**Testing**: pytest com `CliRunner` para fluxo de comando e testes unitários para orquestração e validação de arquivos  
**Target Platform**: CLI local para Linux, macOS e Windows com Python 3.11  
**Project Type**: single-package CLI  
**Performance Goals**: iniciar o processamento de uma entrada válida em uma única execução; gravar cada consolidado exatamente no destino pedido; falhar cedo em entradas inválidas sem desperdiçar processamento remoto  
**Constraints**: internalizar a lógica necessária em `adapta-cli`; não depender do código em `/mnt/c/whatsweb/adapta` em runtime; preservar mensagens curtas sem traceback; manter limpeza best-effort de artefatos temporários e remotos; preservar intermediários úteis em falhas; suportar os modos por arquivo e por diretório sem ambiguidade de parâmetros  
**Scale/Scope**: um arquivo individual por execução no modo simples ou múltiplos arquivos compatíveis por diretório no modo em lote, sete dimensões por item processado, um consolidado final por item e um operador local por vez

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Documentation-First Development**: PASS. O planejamento foi baseado em `docs/features.md`, `docs/arquitetura.md`, `docs/code-map.md`, `docs/modelo-dados.md`, `docs/integracoes.md` e `docs/licoes-aprendidas.md`.
- **Architecture Decisions Must Be Recorded**: PASS. A principal decisão arquitetural é manter a internalização da lógica necessária do destilador dentro do projeto, alinhada à lição já registrada de evitar dependência de código-fonte externo em runtime; nenhum ADR novo é necessário neste estágio.
- **Documentation-First and Test-First Delivery**: PASS. O plano prevê atualização de `docs/` antes da implementação, seguida por TDD em serviços e CLI.
- **Integration and Operational Validation**: PASS. O recurso afeta listagem de arquivos, upload deduplicado, geração remota, limpeza remota e arquivos temporários locais; o plano inclui validação explícita desses fluxos.
- **Simplicity, Consistency, and Learning**: PASS. A solução planejada adiciona um serviço dedicado e modelos mínimos, reusando a arquitetura atual de CLI fina, serviços e cliente interno do Adapta.

**Documentation Impact**:

- `docs/features.md`: adicionar o comando `destilador` com parâmetros `--input`, `--output`, `--input-dir` e `--output-dir`, além dos comandos e fluxos auxiliares de arquivo introduzidos depois.
- `docs/code-map.md`: registrar o novo fluxo de destilação e os módulos internos que passam a conter a lógica internalizada.
- `docs/arquitetura.md`: documentar a ampliação da CLI para um pipeline de destilação por arquivo e a infraestrutura compartilhada de listagem e anexos.
- `docs/modelo-dados.md`: incluir entidades de entrada, dimensões, consolidado, artefatos temporários e metadados de anexos/arquivos remotos.
- `docs/integracoes.md`: detalhar listagem de arquivos, upload deduplicado, processamento remoto e exclusão de artefatos remotos.
- `docs/licoes-aprendidas.md`: somente atualizar se a implementação revelar um incidente novo relevante.
- `docs/adr/`: nenhum novo ADR planejado neste momento.

**Post-Design Re-Check**:

- PASS. O design proposto mantém a regra de internalização do comportamento necessário e não introduz acoplamento novo com código-fonte externo.

## Project Structure

### Documentation (this feature)

```text
specs/004-add-cli-destilador/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── destilador-command.md
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
    ├── logging.py
    ├── models.py
    ├── registry.py
    ├── runtime.py
    └── services/
        ├── output_service.py
        ├── prompt_service.py
        ├── chat_service.py
        ├── debate_service.py
        └── destilador_service.py

tests/
├── integration/
│   ├── test_destilador_command.py
│   ├── test_destilador_directory_command.py
│   └── test_destilador_output_file.py
└── unit/
    ├── test_destilador_service.py
    └── test_cli.py
```

**Structure Decision**: Manter a estrutura única do projeto e internalizar o comportamento do destilador em `src/adapta/services/destilador_service.py`, com apenas as extensões mínimas necessárias em `src/adapta/models.py`, `src/adapta/client.py`, `src/adapta/services/output_service.py` e `src/adapta/cli.py`.

## Complexity Tracking

Nenhuma violação de constituição ou complexidade excepcional identificada neste planejamento.
