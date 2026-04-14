# Feature Specification: Persona Generator

**Feature Branch**: `[001-persona-generator]`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Quero que implemente um gerador de persona com questionário guiado, campos opcionais exceto nome e cargo, geração via modelo Claude com prompt fixo, salvamento em ~/.adapta/persona/{nome-persona}.md, confirmação antes de sobrescrever e exclusão da conversa ao final."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar persona guiada (Priority: P1)

Como usuário da CLI, quero responder um questionário guiado em blocos para gerar uma persona em markdown, mesmo deixando a maior parte dos campos em branco, para obter rapidamente um prompt de persona coerente com os dados que eu realmente forneci.

**Why this priority**: Esse é o fluxo principal de valor da funcionalidade. Sem o questionário guiado e a geração do documento final, a feature não cumpre seu objetivo.

**Independent Test**: Pode ser testado executando o comando da funcionalidade, respondendo pelo menos nome e cargo, deixando os demais campos vazios e verificando que um arquivo markdown válido é gerado com base apenas nos dados preenchidos.

**Acceptance Scenarios**:

1. **Given** que o usuário inicia o gerador de persona, **When** informa um nome válido, informa um cargo e pode pressionar Enter nos demais campos, **Then** o sistema conclui o questionário, gera o conteúdo da persona usando apenas os dados preenchidos e salva o resultado no diretório de personas do usuário.
2. **Given** que o usuário respondeu apenas os campos obrigatórios, **When** a geração for concluída, **Then** o documento final permanece legível, coerente e sem valores inventados para campos vazios.
3. **Given** que o usuário respondeu vários campos opcionais, **When** a geração for concluída, **Then** o documento final inclui somente as seções compatíveis com os dados informados.

---

### User Story 2 - Proteger arquivo existente (Priority: P2)

Como usuário, quero ser avisado quando já existir uma persona com o mesmo nome de arquivo para decidir se desejo sobrescrever, evitando perda acidental de conteúdo já salvo.

**Why this priority**: A proteção contra sobrescrita evita perda de trabalho anterior e reduz risco operacional no uso recorrente do gerador.

**Independent Test**: Pode ser testado criando previamente um arquivo com o mesmo nome de persona, executando novamente o fluxo e verificando que o sistema pede confirmação antes de gravar qualquer alteração.

**Acceptance Scenarios**:

1. **Given** que já existe um arquivo de persona com o mesmo nome de destino, **When** o usuário conclui o questionário, **Then** o sistema pergunta se deseja sobrescrever antes de salvar.
2. **Given** que já existe um arquivo de persona com o mesmo nome de destino, **When** o usuário recusa a sobrescrita, **Then** o arquivo existente permanece inalterado e nenhum novo conteúdo é salvo naquele caminho.
3. **Given** que já existe um arquivo de persona com o mesmo nome de destino, **When** o usuário confirma a sobrescrita, **Then** o sistema substitui o arquivo existente pelo novo resultado gerado.

---

### User Story 3 - Encerrar sessão sem resíduos (Priority: P3)

Como usuário, quero que a conversa temporária usada na geração seja excluída automaticamente ao final para manter o comportamento efêmero da CLI e não deixar sessões remotas abertas.

**Why this priority**: O valor principal já foi entregue após a geração e o salvamento, mas a limpeza automática evita resíduos remotos e mantém consistência com outros fluxos interativos do produto.

**Independent Test**: Pode ser testado executando o fluxo completo e verificando que, após a geração terminar, não resta conversa remota ativa vinculada à execução.

**Acceptance Scenarios**:

1. **Given** que a persona foi gerada com sucesso, **When** o fluxo for encerrado, **Then** a conversa temporária usada na geração é excluída automaticamente.
2. **Given** que a geração falha após iniciar a conversa temporária, **When** o fluxo for encerrado, **Then** o sistema ainda tenta excluir a conversa antes de finalizar.

---

### Edge Cases

- O nome da persona é informado vazio, com apenas espaços ou com caracteres que não podem ser usados com segurança no nome do arquivo.
- O usuário informa o nome de uma persona cujo arquivo de destino já existe.
- O usuário preenche somente `nome` e `cargo`, deixando todos os demais campos em branco.
- O modelo retorna conteúdo incompleto, vazio ou incompatível com a estrutura esperada para o documento de persona.
- A pasta de personas dentro do diretório home do usuário ainda não existe no ambiente atual.
- O comando é executado em Linux ou Windows e o diretório home precisa ser resolvido corretamente sem depender de um separador de caminho específico.
- A limpeza da conversa remota falha depois que o arquivo já foi salvo localmente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST oferecer um fluxo interativo de perguntas organizado nos 6 blocos definidos pelo pedido do usuário, preservando a ordem das perguntas apresentada na descrição da feature.
- **FR-002**: O sistema MUST tratar `nome da persona` e `cargo/título profissional` como campos obrigatórios e permitir que todos os demais campos sejam deixados vazios com Enter.
- **FR-003**: O sistema MUST validar o nome da persona já na primeira pergunta e impedir a continuidade enquanto o nome estiver vazio, contiver apenas espaços ou não puder ser convertido em um nome de arquivo seguro.
- **FR-004**: O sistema MUST usar o nome validado da persona para definir o nome do arquivo final, aplicando uma forma estável e segura para um caminho dentro do diretório home do usuário, no local lógico `~/.adapta/persona/{nome-persona}.md`.
- **FR-005**: O sistema MUST criar automaticamente o diretório de personas dentro do home do usuário quando ele ainda não existir e o usuário prosseguir com a geração.
- **FR-006**: O sistema MUST montar a solicitação de geração com o prompt-base fornecido pelo solicitante e inserir os dados coletados em formato JSON, preservando campos vazios sem preenchimento automático.
- **FR-007**: O sistema MUST gerar o documento final usando apenas os dados fornecidos pelo usuário, sem inventar valores para campos vazios e sem incluir seções incompatíveis com a entrada recebida.
- **FR-008**: O sistema MUST produzir um documento final em markdown que possa ser salvo diretamente como persona reutilizável pelo usuário.
- **FR-009**: O sistema MUST avisar quando o arquivo de destino já existir e MUST solicitar confirmação explícita antes de sobrescrever o conteúdo existente.
- **FR-010**: O sistema MUST cancelar a gravação no caminho de destino quando o usuário rejeitar a sobrescrita.
- **FR-011**: O sistema MUST salvar o resultado final no diretório de personas do usuário, equivalente ao local lógico `~/.adapta/persona/{nome-persona}.md`, após a geração bem-sucedida e após eventual confirmação de sobrescrita.
- **FR-012**: O sistema MUST resolver o diretório home de forma compatível com Linux e Windows, sem depender de expansão textual literal de `~` ou de separadores de caminho fixos.
- **FR-013**: O sistema MUST usar o modelo configurado para esse fluxo de geração de persona sem exigir escolha manual do usuário durante a execução.
- **FR-014**: O sistema MUST tentar excluir a conversa temporária usada para a geração ao final da execução, tanto em caso de sucesso quanto em caso de falha após a abertura da conversa.
- **FR-015**: O sistema MUST informar ao usuário o caminho do arquivo salvo quando a operação for concluída com sucesso.
- **FR-016**: O sistema MUST informar claramente quando a geração não puder ser concluída e MUST evitar salvar um arquivo final vazio ou parcialmente gerado como se estivesse completo.

### Key Entities *(include if feature involves data)*

- **Persona Questionnaire**: Conjunto estruturado de respostas coletadas do usuário, contendo 20 campos organizados em 6 blocos, com `nome` e `cargo` obrigatórios e os demais opcionais.
- **Persona Prompt Request**: Solicitação textual enviada ao gerador contendo o prompt-base fixo e o JSON com os campos preenchidos ou vazios exatamente como foram coletados.
- **Persona Document**: Arquivo markdown final salvo para reutilização futura, derivado exclusivamente das respostas do questionário e da saída gerada para a persona.
- **Temporary Conversation**: Sessão efêmera usada apenas para realizar a geração e que deve ser removida ao término da execução.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos usuários conseguem concluir o fluxo informando somente `nome` e `cargo`, sem serem obrigados a preencher qualquer outro campo.
- **SC-002**: Em testes de aceitação, 100% das execuções que encontram um arquivo existente solicitam confirmação antes de qualquer sobrescrita.
- **SC-003**: Em testes com combinações parciais de respostas, 100% dos documentos gerados deixam de fora campos não preenchidos e não apresentam conteúdo inventado para lacunas.
- **SC-004**: Após uma execução bem-sucedida, o usuário recebe o caminho final do arquivo salvo em 100% dos casos, com resolução correta do diretório home em Linux e Windows.
- **SC-005**: Em testes de encerramento do fluxo, a tentativa de exclusão da conversa temporária ocorre em 100% das execuções que abriram sessão de geração.

## Assumptions

- O gerador será exposto como um fluxo de CLI interativo, alinhado com os demais comandos já existentes no produto.
- O nome informado pelo usuário será normalizado para um identificador de arquivo previsível sem alterar o nome exibido dentro do conteúdo da persona.
- O caminho lógico `~/.adapta/persona/` representa uma pasta sob o diretório home real do usuário e deve ser resolvido corretamente tanto em Linux quanto em Windows.
- A confirmação de sobrescrita ocorrerá apenas quando o caminho de destino final já existir.
- O fluxo utilizará um modelo previamente definido para geração de personas, sem pedir seleção de modelo durante a entrevista.
- Se a exclusão da conversa temporária falhar, o usuário será avisado, mas isso não invalida um arquivo local já salvo com sucesso.

## Documentation Impact *(mandatory)*

- **docs/features.md**: adicionar a nova feature de geração de persona, descrevendo o questionário guiado, o salvamento em `~/.adapta/persona/` e a limpeza da conversa ao final.
- **docs/code-map.md**: atualizar com o novo comando/fluxo principal e os módulos responsáveis pelo questionário, geração e persistência local.
- **docs/arquitetura.md**: atualizar os componentes principais e a comunicação entre CLI, serviço de geração de persona, cliente de chat e persistência local.
- **docs/modelo-dados.md**: documentar as entidades funcionais do questionário de persona, documento final e conversa temporária, caso o projeto mantenha esse mapa de dados.
- **docs/integracoes.md**: atualizar o uso da integração Adapta para refletir a geração de persona por conversa efêmera e sua limpeza ao final.
- **docs/licoes-aprendidas.md**: registrar qualquer incidente relevante descoberto durante implementação, especialmente sobre normalização de nomes, sobrescrita e limpeza remota.
- **docs/adr/**: não requer novo ADR, salvo se a implementação introduzir um novo padrão transversal para fluxos interativos persistidos no diretório do usuário.
