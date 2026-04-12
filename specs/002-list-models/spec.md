# Feature Specification: List Available Models

**Feature Branch**: `[002-list-models]`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: User description: "cria um comando models para listar todos modelos disponiveis"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver modelos disponíveis antes de executar um comando (Priority: P1)

Como pessoa usuária da CLI, quero listar os modelos disponíveis em uma única execução para escolher o modelo correto antes de usar prompt ou chat.

**Why this priority**: Esta é a forma mais direta de reduzir erro de uso e dependência de memória sobre os nomes aceitos pela ferramenta.

**Independent Test**: Pode ser testado executando o comando de listagem em um ambiente configurado e verificando que a saída apresenta todas as opções de modelo disponíveis para uso.

**Acceptance Scenarios**:

1. **Given** que a pessoa executa a listagem de modelos, **When** a CLI processa a solicitação, **Then** ela mostra todas as opções de modelo disponíveis para seleção e uso.
2. **Given** que a listagem é exibida, **When** a pessoa consulta a saída, **Then** ela consegue identificar cada modelo por um nome curto de uso e por uma descrição legível.

---

### User Story 2 - Validar rapidamente se um modelo esperado existe (Priority: P2)

Como pessoa usuária da CLI, quero confirmar se um modelo específico está disponível na ferramenta para evitar tentativas frustradas com nomes inválidos.

**Why this priority**: A verificação rápida reduz erros operacionais e suporte relacionado a nomes de modelo incorretos.

**Independent Test**: Pode ser testado comparando a lista exibida com o catálogo de modelos suportado pela ferramenta e verificando que nenhuma opção ativa ficou oculta.

**Acceptance Scenarios**:

1. **Given** que um modelo está disponível no catálogo da ferramenta, **When** a pessoa executa a listagem, **Then** esse modelo aparece na saída.
2. **Given** que a pessoa procura por um alias conhecido da ferramenta, **When** consulta a listagem, **Then** ela encontra a opção correspondente sem precisar executar outro comando.

---

### User Story 3 - Reaproveitar a listagem em fluxos operacionais e documentação (Priority: P3)

Como pessoa usuária da CLI, quero uma saída estável e legível para reutilizar a listagem em documentação rápida, suporte operacional e conferência manual.

**Why this priority**: Uma saída consistente melhora comunicação entre pessoas usuárias e reduz ambiguidade ao orientar qual modelo deve ser usado.

**Independent Test**: Pode ser testado executando a listagem repetidamente sem alterações no catálogo e verificando que o formato e a ordem permanecem consistentes para leitura humana.

**Acceptance Scenarios**:

1. **Given** que o catálogo de modelos não mudou, **When** a pessoa executa a listagem em momentos diferentes, **Then** a ordem e a apresentação permanecem consistentes.

---

### Edge Cases

- Se não houver nenhum modelo disponível no catálogo, a CLI deve informar isso claramente em vez de retornar saída vazia ambígua.
- Se houver nomes curtos e nomes legíveis muito parecidos, a listagem deve continuar distinguindo as opções de forma compreensível.
- Se a saída for consultada em ambientes de terminal simples, a apresentação deve continuar legível sem depender de formatação especial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST disponibilizar uma forma explícita de listar todos os modelos disponíveis para uso na CLI.
- **FR-002**: O sistema MUST exibir cada modelo disponível usando, no mínimo, um identificador de uso e um nome legível para a pessoa usuária.
- **FR-003**: O sistema MUST incluir na listagem todas as opções de modelo atualmente suportadas pela ferramenta.
- **FR-004**: O sistema MUST apresentar a listagem em formato consistente entre execuções enquanto o catálogo de modelos não mudar.
- **FR-005**: O sistema MUST permitir que a pessoa usuária consulte a listagem sem precisar informar credenciais adicionais, iniciar chat ou enviar prompt.
- **FR-006**: O sistema MUST informar de forma clara quando nenhum modelo estiver disponível para listagem.
- **FR-007**: O sistema MUST manter a listagem alinhada com os mesmos nomes curtos aceitos pelos demais fluxos da CLI.

### Key Entities *(include if feature involves data)*

- **Catalogo de Modelos**: Conjunto das opções de modelo reconhecidas pela CLI como válidas para uso.
- **Entrada de Modelo**: Item individual da listagem, contendo o identificador de uso e a descrição legível apresentada à pessoa usuária.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em testes de aceitação, 100% dos modelos suportados pela ferramenta aparecem na listagem exibida à pessoa usuária.
- **SC-002**: Em testes de usabilidade, a pessoa usuária consegue identificar um modelo válido para uso em até 10 segundos após executar a listagem.
- **SC-003**: Em execuções repetidas sem mudança no catálogo, 100% das listagens mantêm a mesma ordem e estrutura visual.
- **SC-004**: Em testes de suporte operacional, a pessoa usuária consegue confirmar se um modelo esperado existe sem precisar executar prompt ou chat.

## Assumptions

- O catálogo de modelos suportados já existe na ferramenta e pode ser reutilizado para a listagem.
- A feature não altera a forma como prompt e chat resolvem ou validam modelos; ela apenas torna o catálogo visível.
- A primeira versão precisa priorizar leitura humana em terminal comum.
- A listagem deve refletir apenas modelos já suportados pela CLI, não uma descoberta dinâmica externa.

## Documentation Impact *(mandatory)*

- **docs/features.md**: atualizar o mapa funcional para incluir a listagem de modelos como capacidade ativa da CLI.
- **docs/code-map.md**: atualizar a responsabilidade do módulo de CLI e o fluxo relacionado à consulta do catálogo de modelos.
- **docs/arquitetura.md**: atualizar o conjunto de comandos expostos pela CLI sem alterar a arquitetura macro.
- **docs/modelo-dados.md**: sem impacto esperado, salvo se a implementação formalizar novas estruturas conceituais para o catálogo.
- **docs/integracoes.md**: sem impacto esperado, pois a listagem usa o catálogo interno já suportado pela CLI.
- **docs/licoes-aprendidas.md**: atualizar apenas se a implementação revelar inconsistências entre o catálogo exibido e os fluxos de uso real.
- **docs/adr/**: nenhum novo ADR esperado, pois a feature amplia uma capacidade existente sem mudar decisões arquiteturais centrais.
