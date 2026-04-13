# Feature Specification: Comando pipeline por diretório

**Feature Branch**: `[001-cli-pipeline]`  
**Created**: 2026-04-13  
**Status**: Draft  
**Input**: User description: "Quero uma funcionalidade no cli chamada pipeline que aproveite o que o /mnt/c/whatsweb/adapta/src/pipeline.py faz mas receba parametros de entrada input-dir e saida output-dir. mantenha o mesmo formato de entrada e saida, deve usar um banco sqlit semelhante ao original, deixe um caminho default para o banco, mas use uma variavel de ambiente e um parametro para permitir a customização"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Executar pipeline em lote por diretório (Priority: P1)

Como usuário da CLI, quero apontar um diretório de entrada e um diretório de saída para executar o pipeline completo em lote, sem depender de caminhos fixos no projeto.

**Why this priority**: Esse é o objetivo principal da solicitação e entrega valor imediato ao permitir uso operacional do pipeline dentro da CLI existente.

**Independent Test**: Pode ser testado executando o comando `pipeline` com um diretório contendo arquivos compatíveis e verificando se os artefatos esperados são gerados apenas no diretório de saída informado.

**Acceptance Scenarios**:

1. **Given** um diretório de entrada com arquivos compatíveis, **When** o usuário executa o comando `pipeline` com `input-dir` e `output-dir`, **Then** o pipeline processa os arquivos encontrados e grava os resultados no diretório de saída informado.
2. **Given** um diretório de entrada com subpastas e arquivos compatíveis, **When** o comando é executado, **Then** o pipeline inclui os arquivos encontrados na varredura do diretório e gera saídas correspondentes no destino informado.
3. **Given** um lote compatível com o pipeline original, **When** o usuário executa o comando pela CLI, **Then** o formato dos artefatos de entrada aceitos e das saídas produzidas permanece compatível com o fluxo original.

---

### User Story 2 - Controlar destino dos artefatos gerados (Priority: P2)

Como usuário da CLI, quero escolher onde os artefatos do pipeline serão salvos para organizar execuções por lote, ambiente ou cliente sem misturar saídas no diretório padrão do projeto.

**Why this priority**: O valor do novo comando depende de tornar a saída previsível e isolada, reduzindo retrabalho manual após cada execução.

**Independent Test**: Pode ser testado executando duas vezes o comando com o mesmo `input-dir` e `output-dir` diferentes e confirmando que cada execução grava seus artefatos apenas no destino escolhido.

**Acceptance Scenarios**:

1. **Given** um diretório de saída vazio, **When** o pipeline termina com sucesso, **Then** todos os artefatos gerados pela execução ficam disponíveis dentro desse diretório.
2. **Given** um diretório de saída diferente do padrão do projeto, **When** o comando é executado, **Then** o usuário não precisa mover manualmente os resultados para concluir a execução.

---

### User Story 3 - Configurar o banco operacional do pipeline (Priority: P2)

Como usuário da CLI, quero usar um banco SQLite semelhante ao do pipeline original com caminho padrão e opção de sobrescrever esse caminho por variável de ambiente ou parâmetro, para adaptar a execução a diferentes ambientes.

**Why this priority**: O pipeline original depende de persistência operacional; sem uma estratégia clara de banco local e customização, a feature fica difícil de usar em ambientes reais.

**Independent Test**: Pode ser testado executando o comando sem configuração extra, com variável de ambiente configurada e com parâmetro explícito, verificando em cada caso qual caminho de banco foi usado.

**Acceptance Scenarios**:

1. **Given** que o usuário não informou configuração de banco, **When** o comando é executado, **Then** a CLI usa um caminho padrão documentado para o banco SQLite.
2. **Given** que o usuário definiu a variável de ambiente de banco, **When** o comando é executado sem parâmetro explícito de banco, **Then** a CLI usa o caminho definido nessa variável.
3. **Given** que o usuário informou a variável de ambiente e também um parâmetro explícito de banco, **When** o comando é executado, **Then** o parâmetro explícito tem precedência.

---

### User Story 4 - Receber feedback de execução e falhas de entrada (Priority: P3)

Como usuário da CLI, quero receber mensagens claras quando a execução começar, concluir ou falhar por problema de diretório de entrada ou ausência de arquivos compatíveis.

**Why this priority**: Feedback operacional reduz tentativas às cegas e facilita o uso do comando em lotes maiores.

**Independent Test**: Pode ser testado executando o comando com diretório inexistente, diretório vazio e diretório válido, verificando mensagens distintas para cada caso.

**Acceptance Scenarios**:

1. **Given** um `input-dir` inexistente, **When** o usuário executa o comando, **Then** a CLI encerra com mensagem de erro explicando que o diretório de entrada não foi encontrado.
2. **Given** um `input-dir` sem arquivos compatíveis, **When** o usuário executa o comando, **Then** a CLI encerra informando que não há itens processáveis.

---

### Edge Cases

- O que acontece quando o diretório de entrada existe, mas contém apenas arquivos incompatíveis com o pipeline?
- Como o sistema lida com arquivos de mesmo nome em subpastas diferentes durante a geração dos artefatos?
- Como o sistema se comporta quando o diretório de saída já contém resultados de uma execução anterior?
- O que acontece quando parte dos arquivos do lote falha, mas outros arquivos ainda podem ser processados?
- O que acontece quando o caminho do banco configurado aponta para um local sem permissão de escrita?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST expor um comando de CLI chamado `pipeline`.
- **FR-002**: O comando `pipeline` MUST exigir os parâmetros `input-dir` e `output-dir` para iniciar uma execução.
- **FR-003**: O sistema MUST validar que `input-dir` existe e representa um diretório acessível antes de iniciar o processamento.
- **FR-004**: O sistema MUST localizar arquivos compatíveis dentro de `input-dir`, incluindo arquivos encontrados em subdiretórios.
- **FR-005**: O sistema MUST executar o mesmo fluxo funcional já esperado do pipeline atual para cada item elegível encontrado no diretório de entrada.
- **FR-006**: O sistema MUST preservar o mesmo formato de entrada aceito pelo pipeline atual para os tipos de arquivo suportados.
- **FR-007**: O sistema MUST preservar o mesmo formato de saída funcional produzido pelo pipeline atual, apenas redirecionando a persistência para `output-dir` quando aplicável.
- **FR-008**: O sistema MUST gravar os artefatos gerados pela execução dentro de `output-dir`, sem depender de caminhos fixos no diretório raiz do projeto.
- **FR-009**: O sistema MUST criar a estrutura necessária dentro de `output-dir` quando ela ainda não existir.
- **FR-010**: O sistema MUST manter rastreabilidade entre cada arquivo processado e os artefatos produzidos a partir dele.
- **FR-011**: O sistema MUST usar um banco SQLite para persistência operacional semelhante ao pipeline original.
- **FR-012**: O sistema MUST adotar um caminho padrão de banco quando o usuário não informar customização.
- **FR-013**: O sistema MUST permitir customizar o caminho do banco por variável de ambiente.
- **FR-014**: O sistema MUST permitir customizar o caminho do banco por parâmetro explícito do comando.
- **FR-015**: O sistema MUST aplicar precedência determinística entre caminho padrão, variável de ambiente e parâmetro explícito, priorizando o parâmetro explícito.
- **FR-016**: O sistema MUST informar ao usuário o resultado da execução, incluindo sucesso, falha de validação de entrada, ausência de arquivos compatíveis e falha de acesso ao banco configurado.
- **FR-017**: O sistema MUST isolar a saída de uma execução para que o usuário consiga distinguir claramente quais artefatos pertencem ao lote executado.

### Key Entities *(include if feature involves data)*

- **Execução de Pipeline**: representa uma execução única do comando, com diretório de entrada, diretório de saída, status final e conjunto de artefatos produzidos.
- **Documento de Entrada**: representa cada arquivo elegível localizado no diretório informado, incluindo nome, caminho de origem e situação de processamento.
- **Artefato Gerado**: representa cada saída produzida pelo pipeline, vinculada a um documento de entrada e armazenada no diretório de saída escolhido pelo usuário.
- **Banco Operacional**: representa o arquivo SQLite usado pela execução para registrar jobs, estados intermediários e progresso do processamento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das execuções iniciadas com `input-dir` inexistente ou inválido terminam com mensagem de erro clara antes de qualquer processamento.
- **SC-002**: 100% das execuções bem-sucedidas gravam seus artefatos exclusivamente dentro do `output-dir` informado pelo usuário.
- **SC-003**: 100% das execuções sem configuração explícita de banco usam o caminho padrão documentado, e 100% das execuções com variável de ambiente ou parâmetro usam a precedência configurada corretamente.
- **SC-004**: Em um lote de teste com múltiplos arquivos compatíveis, pelo menos 95% dos arquivos elegíveis concluem processamento sem intervenção manual quando o ambiente externo está saudável.
- **SC-005**: Um usuário recorrente consegue iniciar uma nova execução do pipeline informando apenas `input-dir` e `output-dir`, sem precisar mover arquivos manualmente antes ou depois da execução.

## Assumptions

- O novo comando atenderá o mesmo perfil de usuário já atendido pelos demais comandos operacionais da CLI.
- O escopo inicial cobre apenas processamento por diretório; execução por arquivo único não faz parte desta solicitação.
- Os tipos de arquivo compatíveis permanecem os mesmos que o pipeline atual já aceita hoje.
- O pipeline continuará dependendo das integrações externas e credenciais já necessárias para a execução atual.
- O diretório de saída pode ser criado automaticamente pela CLI quando ainda não existir.
- O banco SQLite continuará sendo um detalhe operacional local da CLI, sem necessidade de serviço externo adicional.
- A customização do banco seguirá a convenção já usada no projeto para configuração por variável de ambiente e opção explícita de comando.

## Documentation Impact *(mandatory)*

- **docs/features.md**: deve incluir a nova feature `pipeline`, descrevendo execução por `input-dir` e `output-dir` e sua relação com o pipeline existente.
- **docs/code-map.md**: deve registrar o novo comando na CLI e o serviço ou fluxo responsável por encapsular a execução do pipeline.
- **docs/arquitetura.md**: deve ser atualizado para citar o novo fluxo operacional do comando `pipeline` caso ele introduza um serviço dedicado ou uma nova orquestração.
- **docs/modelo-dados.md**: deve refletir a entidade operacional de banco do pipeline e a relação entre execução, documentos processados e artefatos gerados.
- **docs/integracoes.md**: deve refletir que a CLI passa a expor o pipeline existente como fluxo operacional com diretórios de entrada e saída configuráveis e persistência local em SQLite.
- **docs/licoes-aprendidas.md**: deve registrar qualquer incidente relevante encontrado durante a internalização do pipeline, especialmente conflitos de caminhos, limpeza de artefatos ou processamento parcial.
- **docs/adr/**: não requer novo ADR por padrão; só será necessário se a implementação exigir mudança arquitetural relevante para encapsular o pipeline legado.
