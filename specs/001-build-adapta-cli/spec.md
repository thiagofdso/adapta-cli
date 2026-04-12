# Feature Specification: Build Adapta CLI

**Feature Branch**: `[###-feature-name]`  
**Created**: 2026-04-11  
**Status**: Draft  
**Input**: User description: "analise o projeto adapta em especial /mnt/c/whatsweb/adapta/src/generators_v2 e /mnt/c/whatsweb/adapta/src/config.py e crie na pasta adapta-cli um projeto python que use os modelos da mesma forma, nao precisa usar o nome generator, reformule a estrutura conforme necessario, quero poder chamar via terminal e enviar um prompt e receber a resposta direto no terminal exemplo adapta prompt -model gpt -prompt \"me explique o que é ia\" ou enviando um arquivo adapta -model gpt -prompt-file prompt.txt ou passando parâmetro -output saída.txt para salvar a resposta em arquivo e também quero poder conversar por chat adapta chat -model para o chat considere o arquivo /mnt/c/whatsweb/adapta/src/app_chat.py para aproveitar como funciona. Quero que considere as variáveis de ambiente do config para autenticação uma variável ADAPTA_MODEL para usar como modelo default quando o usuario não informar o parâmetro, caso não informe e não exista variável em qualquer um dos comandos deve aparecer as opções de modelo para selecionar e responder ou iniciar o chat, importante apos cada sessão deve ser excluído o chat na adapta."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Executar um prompt único pelo terminal (Priority: P1)

Como pessoa usuária da linha de comando, quero enviar um prompt diretamente no terminal ou por arquivo para receber uma resposta imediata sem abrir uma interface interativa.

**Why this priority**: Este é o fluxo principal de valor: consultar um modelo rapidamente a partir do terminal.

**Independent Test**: Pode ser testado executando um comando com prompt em linha ou arquivo e verificando que a resposta é exibida no terminal ou gravada no destino solicitado.

**Acceptance Scenarios**:

1. **Given** que a pessoa informa um modelo e um texto no comando, **When** executa a operação de prompt, **Then** a resposta é retornada diretamente no terminal.
2. **Given** que a pessoa informa um arquivo de prompt válido, **When** executa a operação de prompt, **Then** o conteúdo do arquivo é usado como entrada e a resposta é retornada.
3. **Given** que a pessoa informa um destino de saída, **When** a resposta é gerada, **Then** o conteúdo é salvo no arquivo indicado além de ficar disponível para consulta pela pessoa usuária.

---

### User Story 2 - Conversar em modo chat (Priority: P2)

Como pessoa usuária da linha de comando, quero iniciar uma conversa contínua com um modelo para enviar múltiplas mensagens na mesma sessão sem repetir toda a configuração a cada rodada.

**Why this priority**: O chat amplia o uso da ferramenta para interações iterativas, mas depende do fluxo principal de seleção de modelo e autenticação já estar funcional.

**Independent Test**: Pode ser testado iniciando uma sessão de chat, trocando mensagens sucessivas e confirmando que a sessão é encerrada e removida ao final.

**Acceptance Scenarios**:

1. **Given** que a pessoa inicia o comando de chat com um modelo definido, **When** envia mensagens sucessivas, **Then** cada resposta considera o contexto acumulado da sessão atual.
2. **Given** que a pessoa encerra o chat, **When** a sessão termina, **Then** a conversa correspondente é excluída do sistema remoto para não permanecer ativa após o uso.

---

### User Story 3 - Selecionar um modelo padrão ou interativo (Priority: P3)

Como pessoa usuária da linha de comando, quero que a ferramenta escolha automaticamente o modelo configurado por parâmetro ou ambiente e, quando isso não acontecer, me ofereça uma seleção guiada para continuar sem erro confuso.

**Why this priority**: Reduz atrito no uso diário e evita falhas quando o modelo não é informado explicitamente.

**Independent Test**: Pode ser testado executando os comandos sem parâmetro de modelo em diferentes cenários de configuração e verificando a escolha automática ou a lista de opções.

**Acceptance Scenarios**:

1. **Given** que a pessoa não informa um modelo no comando, **When** existe um modelo padrão configurado em ambiente, **Then** esse modelo é utilizado automaticamente.
2. **Given** que a pessoa não informa um modelo e nenhum padrão está configurado, **When** inicia um comando de prompt ou chat, **Then** a ferramenta apresenta as opções disponíveis para seleção antes de prosseguir.

---

### Edge Cases

- O comando deve falhar com mensagem clara quando a pessoa informar simultaneamente prompt em linha e arquivo de prompt.
- O comando deve falhar com mensagem clara quando o arquivo de prompt não existir, estiver vazio ou não puder ser lido.
- O comando deve interromper a execução com orientação objetiva quando não houver credenciais válidas no ambiente.
- O comando deve informar de forma compreensível quando o modelo solicitado não estiver disponível.
- Se a exclusão da sessão de chat falhar ao encerrar, a pessoa usuária deve ser avisada de que a limpeza não foi concluída.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST disponibilizar um comando de linha de comando para envio de prompt único e retorno da resposta no terminal.
- **FR-002**: O sistema MUST permitir que a entrada do prompt seja fornecida diretamente por argumento ou por um arquivo de texto.
- **FR-003**: O sistema MUST impedir o uso simultâneo de prompt direto e arquivo de prompt na mesma execução.
- **FR-004**: O sistema MUST permitir que a pessoa usuária informe explicitamente qual modelo deseja usar em qualquer comando suportado.
- **FR-005**: O sistema MUST usar o valor da variável de ambiente `ADAPTA_MODEL` como modelo padrão quando o parâmetro de modelo não for informado.
- **FR-006**: O sistema MUST apresentar uma lista de modelos disponíveis para seleção quando nenhum modelo for informado e não existir modelo padrão configurado.
- **FR-007**: O sistema MUST usar as variáveis de ambiente já adotadas pelo sistema Adapta para autenticação e acesso aos modelos.
- **FR-008**: O sistema MUST permitir salvar a resposta gerada em um arquivo definido pela pessoa usuária.
- **FR-009**: O sistema MUST disponibilizar um comando de chat interativo que mantenha o contexto durante a sessão ativa.
- **FR-010**: O sistema MUST encerrar e excluir a sessão de chat remota ao final de cada conversa.
- **FR-011**: O sistema MUST informar erros de uso, autenticação, seleção de modelo, leitura de arquivo e gravação de saída com mensagens claras e acionáveis.
- **FR-012**: O sistema MUST preservar comportamento consistente entre os comandos de prompt único e chat para resolução de modelo, autenticação e tratamento de erros.
- **FR-013**: O sistema MUST permitir que a pessoa usuária defina o nível de log por parâmetro de linha de comando em cada execução.
- **FR-014**: O sistema MUST operar sem emitir logs operacionais por padrão.
- **FR-015**: O sistema MUST incluir uma forma padronizada de instalação que registre `adapta` como comando disponível no sistema.
- **FR-016**: O sistema MUST permitir instalação usando os arquivos locais do projeto e também a partir de um repositório remoto informado pela pessoa usuária.
- **FR-017**: O sistema MUST incluir um `Makefile` com atalhos para executar testes e para acionar os fluxos principais da CLI.
- **FR-018**: O sistema MUST oferecer alvos mínimos de `make` para prompt e chat, permitindo uso simples como `make prompt` e `make chat`.

### Key Entities *(include if feature involves data)*

- **Modelo**: Opção de IA que pode ser selecionada explicitamente, herdada do ambiente ou escolhida interativamente antes da execução.
- **Solicitação de Prompt**: Entrada de uso único composta pelo texto do prompt, origem do conteúdo, modelo escolhido e destino opcional de saída.
- **Sessão de Chat**: Conversa temporária com contexto acumulado durante múltiplas mensagens e que deve ser removida ao término.
- **Configuração de Ambiente**: Conjunto de variáveis necessárias para autenticação e definição opcional do modelo padrão.
- **Configuração de Execução**: Conjunto de opções transitórias da execução, incluindo ativação opcional de logs e seu nível.
- **Origem de Instalação**: Referência usada para instalar a CLI, podendo apontar para o diretório local do projeto ou para um repositório remoto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em testes de aceitação, 100% dos comandos de prompt único com parâmetros válidos retornam uma resposta utilizável sem exigir interação adicional além da esperada.
- **SC-002**: Em testes de aceitação, 100% das execuções sem modelo explícito utilizam o modelo padrão configurado ou apresentam uma seleção de modelos antes de continuar.
- **SC-003**: Em testes de uso, a pessoa usuária consegue iniciar um chat e trocar pelo menos 3 mensagens consecutivas mantendo contexto sem reiniciar a sessão.
- **SC-004**: Em testes de encerramento de chat, 100% das sessões finalizadas resultam em remoção confirmada da conversa ou em aviso explícito de falha de limpeza.
- **SC-005**: Em testes de usabilidade, a pessoa usuária consegue executar os três fluxos principais, prompt inline, prompt por arquivo e chat, em até 1 minuto cada usando apenas a ajuda do comando.
- **SC-006**: Em testes de aceitação, 100% das execuções sem parâmetro de log não emitem logs operacionais e 100% das execuções com `--log` refletem o nível solicitado.
- **SC-007**: Em testes de instalação, a pessoa usuária consegue disponibilizar o comando `adapta` no sistema a partir de origem local e de origem remota seguindo um único fluxo documentado por opção.
- **SC-008**: Em testes de usabilidade local, a pessoa usuária consegue executar `make test`, `make prompt` e `make chat` seguindo a ajuda documentada sem memorizar comandos internos do projeto.

## Assumptions

- A nova CLI deve reutilizar as mesmas credenciais e regras de autenticação já esperadas pelo ecossistema Adapta.
- A lista de modelos disponíveis pode ser obtida a partir da mesma fonte já utilizada pelo sistema Adapta atual.
- O escopo desta funcionalidade cobre uso local via terminal por uma única pessoa usuária por vez.
- A saída salva em arquivo deve conter o mesmo conteúdo textual principal retornado no terminal para a mesma execução.
- A ausência de logs por padrão não deve ocultar a resposta principal do comando nem mensagens finais indispensáveis para uso seguro.
- A instalação remota pode depender de conectividade com o repositório informado e de ferramentas padrão já disponíveis na máquina da pessoa usuária.
- Os alvos do `Makefile` podem depender de variáveis informadas na invocação para personalizar modelo, prompt e demais opções sem duplicar regras de negócio.
