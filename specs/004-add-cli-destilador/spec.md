# Feature Specification: Destilador no CLI

**Feature Branch**: `[004-add-cli-destilador]`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: User description: "Quero uma funcionalidade no cli chamada destilador que aproveite o que o /mnt/c/whatsweb/adapta/src/destilador.py faz mas receba parametros de entrada input e saida output."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Destilar uma entrada informada pelo usuário (Priority: P1)

Como operador do CLI, quero informar um arquivo de entrada e um destino de saída, ou um diretório de entrada e um diretório de saída, para gerar material consolidado sem depender de pastas fixas embutidas no comando.

**Why this priority**: Este é o núcleo de valor da funcionalidade, porque transforma o fluxo atual em um comando reutilizável e previsível no terminal.

**Independent Test**: Pode ser testado executando o comando `destilador` com `--input` e `--output`, ou com `--input-dir` e `--output-dir`, confirmando que o conteúdo consolidado é gerado no destino solicitado.

**Acceptance Scenarios**:

1. **Given** que o usuário informa um arquivo válido em `--input` e um caminho de saída em `--output`, **When** executa o comando `destilador`, **Then** o sistema deve processar o arquivo e gravar o resultado final no destino informado.
2. **Given** que o usuário informa um diretório válido em `--input-dir` e um diretório de saída em `--output-dir`, **When** executa o comando `destilador`, **Then** o sistema deve processar os arquivos compatíveis encontrados e gravar um consolidado por item no diretório informado.
3. **Given** que o processamento das 7 dimensões termina com sucesso, **When** o comando conclui a execução, **Then** o sistema deve produzir um arquivo final consolidado para cada item de entrada processado.
4. **Given** que o usuário informa um caminho de saída existente, **When** o comando termina com sucesso, **Then** o sistema deve atualizar o arquivo de saída com o resultado mais recente.

---

### User Story 2 - Receber erros acionáveis para entradas inválidas (Priority: P2)

Como operador do CLI, quero mensagens claras quando o arquivo de entrada, o diretório de entrada, o arquivo de saída ou o diretório de saída forem inválidos para corrigir o comando sem depuração manual.

**Why this priority**: Sem validação de entrada, o comando fica difícil de usar e falhas simples se transformam em suporte manual.

**Independent Test**: Pode ser testado executando o comando com arquivo de entrada inexistente, diretório inexistente, tipo de arquivo inválido ou saída não gravável e verificando mensagens curtas e acionáveis.

**Acceptance Scenarios**:

1. **Given** que o usuário informa um caminho inexistente em `--input` ou `--input-dir`, **When** executa o comando, **Then** o sistema deve interromper a execução antes do processamento e informar que a origem não foi encontrada.
2. **Given** que o usuário informa uma combinação inválida de parâmetros de entrada ou saída, **When** executa o comando, **Then** o sistema deve rejeitar o comando com instrução clara de correção.
3. **Given** que o usuário informa um arquivo de entrada incompatível com o processamento esperado, **When** executa o comando, **Then** o sistema deve rejeitar a entrada com instrução clara de correção.
4. **Given** que o caminho de `--output` ou `--output-dir` não pode ser criado ou sobrescrito, **When** o processamento tenta persistir o resultado, **Then** o sistema deve informar a falha de gravação sem esconder o motivo.

---

### User Story 3 - Preservar o comportamento operacional do destilador existente (Priority: P3)

Como operador do CLI, quero que o comando siga o fluxo de destilação já conhecido, incluindo consolidação por dimensões, reutilização segura de uploads, possibilidade de inspecionar arquivos remotos já existentes e limpeza operacional compatível, com toda a lógica necessária internalizada no próprio projeto, para aproveitar um processo já validado sem depender de código externo.

**Why this priority**: Garante continuidade do processo atual sem reintroduzir trabalho manual ou alterar a lógica funcional essencial do destilador.

**Independent Test**: Pode ser testado executando o comando com uma entrada válida e verificando que o fluxo percorre as dimensões esperadas, produz a consolidação final e mantém o tratamento de limpezas e falhas parciais.

**Acceptance Scenarios**:

1. **Given** que o usuário inicia uma destilação válida, **When** o comando executa o processo completo, **Then** o sistema deve preservar a geração por dimensões antes da consolidação final.
2. **Given** que o processamento conclui com sucesso, **When** os artefatos temporários não forem mais necessários, **Then** o sistema deve limpá-los conforme o comportamento operacional da rotina existente.
3. **Given** que ocorrer uma falha durante a execução, **When** o comando encerra, **Then** o sistema deve preservar material intermediário útil para análise quando aplicável.
4. **Given** que um arquivo remoto com o mesmo nome já existe na conta, **When** o `destilador` precisa anexá-lo ao fluxo, **Then** o sistema deve consultar a listagem remota antes do upload e reaproveitar o arquivo existente em vez de reenviá-lo.

---

### Edge Cases

- O que acontece quando `--input` aponta para um arquivo inexistente?
- O que acontece quando `--input-dir` aponta para um diretório inexistente ou sem arquivos compatíveis?
- Como o sistema reage quando o arquivo de entrada existe, mas não pode ser lido?
- O que acontece quando `--output` aponta para um diretório inexistente ou sem permissão de escrita?
- O que acontece quando `--output-dir` aponta para um diretório inexistente ou sem permissão de escrita?
- Como o sistema reage quando o usuário mistura parâmetros incompatíveis, como `--input` com `--output-dir`?
- Como o sistema se comporta quando a destilação falha em uma ou mais dimensões e não consegue produzir um consolidado final?
- O que acontece quando o usuário interrompe manualmente a execução?
- Como o sistema lida com um arquivo de saída já existente?
- Como o sistema lida com arquivos remotos já enviados anteriormente com o mesmo nome do arquivo atual?
- Como o operador inspeciona os arquivos remotos existentes antes de iniciar um fluxo baseado em upload?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST disponibilizar um comando de CLI chamado `destilador`.
- **FR-002**: O comando `destilador` MUST aceitar um parâmetro `--input` para receber o arquivo de entrada a ser processado.
- **FR-003**: O comando `destilador` MUST aceitar um parâmetro `--output` para receber o caminho do arquivo final consolidado.
- **FR-004**: O comando `destilador` MUST aceitar um parâmetro `--input-dir` para receber um diretório de entrada com múltiplos arquivos compatíveis.
- **FR-005**: O comando `destilador` MUST aceitar um parâmetro `--output-dir` para receber o diretório onde serão gravados os arquivos consolidados do processamento em lote.
- **FR-006**: O sistema MUST aceitar o modo por arquivo (`--input` com `--output`) e o modo por diretório (`--input-dir` com `--output-dir`).
- **FR-007**: O sistema MUST rejeitar combinações incompatíveis entre parâmetros de arquivo e diretório e informar como corrigir o comando.
- **FR-008**: O sistema MUST validar que `--input` aponta para um arquivo existente ou que `--input-dir` aponta para um diretório existente antes de iniciar o processamento.
- **FR-009**: O sistema MUST rejeitar entradas incompatíveis com o tipo de processamento esperado e informar como corrigir o comando.
- **FR-010**: O sistema MUST validar que o caminho de `--output` ou `--output-dir` pode ser criado, usado ou sobrescrito antes de concluir a persistência do resultado final.
- **FR-011**: O comando MUST internalizar no `adapta-cli` o fluxo funcional necessário do destilador para gerar conteúdo intermediário por dimensões antes da consolidação final.
- **FR-012**: No modo por arquivo, o sistema MUST consolidar as dimensões geradas em um único arquivo final no caminho definido em `--output`.
- **FR-013**: No modo por diretório, o sistema MUST processar cada arquivo compatível encontrado em `--input-dir` e gravar um arquivo final consolidado correspondente em `--output-dir`.
- **FR-014**: O sistema MUST preservar a lógica atual de tratamento de falhas parciais durante a geração das dimensões, incluindo repetição quando necessário.
- **FR-015**: O sistema MUST manter a limpeza operacional compatível com a rotina atual para arquivos temporários e artefatos remotos após execuções bem-sucedidas.
- **FR-016**: O sistema MUST preservar artefatos intermediários relevantes quando a execução falhar ou for interrompida, desde que isso ajude a análise posterior.
- **FR-017**: O sistema MUST informar mensagens curtas e acionáveis para erros de validação, leitura, processamento e gravação.
- **FR-018**: O sistema MUST permitir sobrescrever o arquivo indicado em `--output` ou atualizar arquivos correspondentes em `--output-dir` quando a execução concluir com sucesso.
- **FR-019**: O cliente interno MUST disponibilizar listagem paginada de arquivos remotos já existentes na conta para suportar inspeção operacional e decisões de upload.
- **FR-020**: Antes de subir um arquivo para fluxos como `destilador`, o cliente MUST consultar a listagem remota e reaproveitar o arquivo existente quando encontrar o mesmo nome.
- **FR-021**: O sistema MUST disponibilizar um comando `list-files` para exibir no terminal os arquivos remotos existentes com metadados operacionais básicos.
- **FR-022**: Os comandos de CLI baseados em conversa que aceitam anexos MUST validar de 1 a 5 arquivos separados por vírgula antes de iniciar chamadas remotas.
- **FR-023**: O comando `debate` MUST reutilizar um upload único dos anexos configurados em `--file` ao longo de todas as rodadas e agentes da execução.

### Key Entities *(include if feature involves data)*

- **Arquivo de Entrada**: documento informado pelo usuário em `--input` ou localizado em `--input-dir` e usado como fonte da destilação.
- **Lote de Entrada**: conjunto de arquivos compatíveis encontrados em `--input-dir` para processamento em sequência.
- **Dimensão de Destilação**: resultado intermediário gerado para cada uma das dimensões do processo antes da consolidação final.
- **Arquivo Consolidado**: saída final produzida em `--output` ou em `--output-dir` após combinar as dimensões geradas com sucesso.
- **Artefato Temporário**: arquivo local ou remoto usado durante o processamento e sujeito a limpeza ou preservação conforme o resultado da execução.
- **Arquivo Remoto Listado**: metadado retornado pela listagem remota, contendo nome, caminho, tipo e tamanho para inspeção e possível reaproveitamento.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das execuções com `--input` e `--output` válidos, ou com `--input-dir` e `--output-dir` válidos, iniciam o processamento sem exigir configuração de pastas fixas.
- **SC-002**: 100% das entradas inválidas ou combinações inválidas de parâmetros de entrada e saída são rejeitadas antes da conclusão do comando com uma mensagem acionável.
- **SC-003**: Usuários conseguem produzir um arquivo consolidado por documento válido em uma única execução do comando, tanto no modo por arquivo quanto no modo por diretório.
- **SC-004**: Em execuções bem-sucedidas, cada arquivo final é gravado exatamente no caminho solicitado pelo usuário ou no diretório de saída correspondente.
- **SC-005**: Em falhas operacionais, o usuário consegue identificar se houve preservação de material intermediário para análise sem inspecionar código-fonte.
- **SC-006**: Em uploads repetidos do mesmo nome, o sistema evita reenvio redundante sempre que a listagem remota já contiver o arquivo necessário.
- **SC-007**: O operador consegue inspecionar via `list-files` os arquivos remotos já disponíveis sem recorrer ao navegador.

## Assumptions

- O comando continuará processando um arquivo de entrada por execução, em vez de múltiplos documentos em lote.
- Além do modo por arquivo individual, o comando também suportará processamento em lote por diretório, preservando o contrato explícito de entrada e saída.
- O tipo principal de entrada esperado continuará sendo compatível com o fluxo atual do destilador existente.
- O caminho informado em `--output` representa o arquivo final consolidado, e não apenas um diretório-base.
- Quando `--output-dir` for usado, o sistema derivará um arquivo final por item processado usando convenção consistente de nome baseada no arquivo de entrada.
- A lógica principal de destilação por 7 dimensões já é considerada válida e deve ser internalizada no projeto, não acessada a partir de outro código-fonte em runtime.
- O usuário já possui credenciais e ambiente preparados para executar comandos que dependem do serviço externo associado ao destilador.

## Documentation Impact *(mandatory)*

- **docs/features.md**: registrar `destilador`, `list-files` e os comandos com suporte a anexos por `--file`.
- **docs/code-map.md**: registrar o novo fluxo CLI e os módulos que passam a orquestrar a destilação.
- **docs/arquitetura.md**: documentar a extensão do CLI para fluxos baseados em arquivo, incluindo listagem e reaproveitamento de uploads.
- **docs/modelo-dados.md**: incluir entidades de entrada, dimensões, artefato consolidado, anexos e arquivos remotos listados se a implementação as formalizar no projeto.
- **docs/integracoes.md**: atualizar o uso de listagem, upload deduplicado e anexos em comandos conversacionais.
- **docs/licoes-aprendidas.md**: registrar incidentes relevantes encontrados ao adaptar o processo existente para o CLI.
- **docs/adr/**: nenhum ADR é assumido como obrigatório neste estágio; criar apenas se a adaptação exigir nova decisão arquitetural significativa.
