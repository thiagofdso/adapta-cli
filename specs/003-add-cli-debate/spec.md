# Feature Specification: Debate no CLI

**Feature Branch**: `[003-add-cli-debate]`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: User description: "[PasQuero uma funcionalidade no cli chamada debate que aproveite o que o /mnt/c/whatsweb/adapta/src/app_debate.py, ele pode receber o parametro --config com um json no formato abaixo.

{[
    \"A1\": {\"model\":\"claude\",\"prompt\":\"voce é um arquiteto de ti\"},
    \"A2\": {\"model\":\"claude\",\"prompt\":\"voce é um desenvolvedor\"}
]}

um parametro --rounds que indica o numero de rodadas de debate
--output para indicar que quer guardar o resultado em um arquivo senao gere no terminal
--prompt para passar o prompt do debate
--model-conclusion para indicar o modulo que vai fazer a conclusao final por padrao use o gemini

caso o usuario nao informe o --config deve primeiro perguntar o numero de agentes, entao começar com a seleção do modelo do primeiro agente, o prompt dele e assim sucessivamente para todos agentes, sendo no minimo 2 agentes, se nao passar o numero de rodadas deve perguntar tambem, sempre valide as entradas para ver se é numero quando precisa (rodada numero de agentes), salve o arquivo debate.json quando isso ocorrer. o usuario tambem pode configurar a variavel de ambiente ADAPTA_DEBATE_CONFIG use ela se existir, senao existir nem a variavel nem o valor do parametro --config sempre siga esse processo de fazer perguntas. Quando nao for gravar arquivo (sem --output) exiba as respostas a medida que for gerada de cada agente, lembre de identificar ex Agente 1 Rodada 1"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Executar debate configurado por arquivo (Priority: P1)

Como operador do CLI, quero iniciar um debate multiagente a partir de uma configuração pronta para obter contribuições de vários perfis e uma conclusão final sem precisar responder perguntas interativas.

**Why this priority**: Este é o fluxo mais direto para automação, repetibilidade e uso em scripts locais.

**Independent Test**: Pode ser testado informando um arquivo de configuração válido, um tema de debate e o número de rodadas, confirmando que o debate inicia, executa todos os agentes e produz uma conclusão final.

**Acceptance Scenarios**:

1. **Given** que o usuário informa `--config`, `--prompt` e `--rounds`, **When** executa o comando `debate`, **Then** o sistema deve carregar os agentes do arquivo, executar as rodadas solicitadas e gerar a conclusão final.
2. **Given** que o usuário informa `--config` e não informa `--model-conclusion`, **When** o debate termina, **Then** o sistema deve usar o modelo de conclusão padrão definido para a funcionalidade.
3. **Given** que o usuário informa `--output`, **When** o debate termina com sucesso, **Then** o sistema deve persistir o resultado completo no arquivo indicado.

---

### User Story 2 - Montar debate interativamente sem arquivo prévio (Priority: P2)

Como operador do CLI, quero ser guiado por perguntas quando não houver configuração disponível para montar um debate válido sem editar arquivos manualmente.

**Why this priority**: Garante uso acessível da funcionalidade por pessoas que estão explorando o recurso pela primeira vez ou criando debates ocasionais.

**Independent Test**: Pode ser testado iniciando o comando sem `--config` e sem configuração em ambiente, respondendo às perguntas de agentes, modelos, prompts e rodadas até que o arquivo `debate.json` seja criado e utilizado na execução.

**Acceptance Scenarios**:

1. **Given** que o usuário não informa `--config` e não existe `ADAPTA_DEBATE_CONFIG`, **When** executa o comando `debate`, **Then** o sistema deve perguntar a quantidade de agentes, exigir no mínimo 2 e coletar modelo e prompt para cada agente.
2. **Given** que o usuário não informa `--rounds`, **When** executa o fluxo interativo, **Then** o sistema deve solicitar o número de rodadas e validar que a resposta é numérica.
3. **Given** que o usuário conclui a configuração interativa, **When** o sistema termina a coleta, **Then** o sistema deve salvar a configuração montada em `debate.json` para reutilização futura.

---

### User Story 3 - Acompanhar o debate em tempo real no terminal (Priority: P3)

Como operador do CLI, quero ver as respostas sendo exibidas conforme são geradas quando não solicito arquivo de saída para acompanhar a evolução do debate rodada a rodada.

**Why this priority**: Melhora a experiência de uso interativo e reduz a sensação de espera em debates mais longos.

**Independent Test**: Pode ser testado executando um debate sem `--output` e verificando que cada resposta aparece no terminal com identificação de agente e rodada antes da conclusão final.

**Acceptance Scenarios**:

1. **Given** que o usuário executa o debate sem `--output`, **When** cada agente conclui sua resposta em uma rodada, **Then** o sistema deve exibir imediatamente o conteúdo no terminal com identificação do agente e da rodada.
2. **Given** que um agente retorna erro ou resposta vazia, **When** o sistema processa a rodada, **Then** o terminal deve mostrar uma mensagem identificando qual agente e qual rodada foram afetados.

---

### Edge Cases

- O que acontece quando o arquivo informado em `--config` não existe, não pode ser lido ou contém JSON inválido?
- Como o sistema reage quando a configuração define menos de 2 agentes?
- Como o sistema reage quando `--rounds` ou a resposta interativa para quantidade de agentes/rodadas não é numérica ou é menor que o mínimo aceito?
- O que acontece quando `ADAPTA_DEBATE_CONFIG` aponta para um arquivo inexistente ou inválido?
- Como o sistema trata falhas parciais, como um agente responder com erro enquanto os demais completam a rodada?
- Como o sistema se comporta quando o usuário informa `--output` sem permissão de escrita no caminho desejado?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST disponibilizar um comando de CLI chamado `debate` para conduzir debates com múltiplos agentes sobre um prompt informado pelo usuário.
- **FR-002**: O comando `debate` MUST aceitar um parâmetro `--config` para carregar a definição dos agentes a partir de um arquivo JSON.
- **FR-003**: O sistema MUST aceitar a variável de ambiente `ADAPTA_DEBATE_CONFIG` como fonte de configuração quando `--config` não for informado.
- **FR-004**: O sistema MUST priorizar `--config` sobre `ADAPTA_DEBATE_CONFIG` quando ambos estiverem definidos.
- **FR-005**: A configuração de agentes MUST permitir informar, para cada agente, ao menos um identificador, um modelo e um prompt de atuação.
- **FR-006**: O sistema MUST rejeitar configurações com menos de 2 agentes e informar ao usuário como corrigir a entrada.
- **FR-007**: O comando `debate` MUST aceitar `--rounds` para definir o número de rodadas do debate.
- **FR-008**: Quando `--rounds` não for informado, o sistema MUST solicitar interativamente o número de rodadas e validar que a entrada é numérica e maior que zero.
- **FR-009**: Quando não existir nem `--config` nem `ADAPTA_DEBATE_CONFIG`, o sistema MUST iniciar um fluxo interativo para coletar quantidade de agentes, modelo e prompt de cada agente.
- **FR-010**: No fluxo interativo, o sistema MUST solicitar a quantidade de agentes antes das demais perguntas e validar que a entrada é numérica e maior ou igual a 2.
- **FR-011**: No fluxo interativo, o sistema MUST coletar o modelo e o prompt individualmente para cada agente, em sequência, até completar todos os agentes informados.
- **FR-012**: Após concluir a configuração interativa, o sistema MUST salvar a definição dos agentes em um arquivo local chamado `debate.json`.
- **FR-013**: O comando `debate` MUST aceitar `--prompt` para receber o tema ou problema que será debatido.
- **FR-014**: O sistema MUST impedir a execução do debate quando o prompt principal não for informado por parâmetro ou interação equivalente.
- **FR-015**: O comando `debate` MUST aceitar `--model-conclusion` para definir o modelo responsável pela conclusão final.
- **FR-016**: Quando `--model-conclusion` não for informado, o sistema MUST usar Gemini como padrão para a conclusão final.
- **FR-017**: O sistema MUST executar o debate por rodadas, produzindo uma resposta por agente em cada rodada antes de gerar a conclusão final.
- **FR-018**: Quando `--output` for informado, o sistema MUST gravar o resultado completo do debate no arquivo solicitado.
- **FR-019**: Quando `--output` não for informado, o sistema MUST exibir as respostas no terminal à medida que forem geradas.
- **FR-020**: As saídas exibidas no terminal MUST identificar claramente o agente e a rodada de cada resposta, usando um formato equivalente a `Agente 1 Rodada 1`.
- **FR-021**: Ao final do debate, o sistema MUST gerar uma conclusão consolidada a partir das contribuições finais dos agentes.
- **FR-022**: O sistema MUST informar erros de configuração, validação, leitura e gravação com mensagens acionáveis para o usuário.

### Key Entities *(include if feature involves data)*

- **Configuração de Debate**: conjunto de definições necessárias para iniciar um debate, incluindo agentes, número de rodadas, prompt principal, modelo de conclusão e destino opcional de saída.
- **Agente de Debate**: participante individual do debate, com identificador, modelo selecionado e instruções próprias.
- **Rodada de Debate**: ciclo numerado no qual todos os agentes respondem ao mesmo tema considerando o contexto acumulado até aquele ponto.
- **Resultado de Debate**: registro final que reúne respostas por rodada, identificação dos agentes e a conclusão consolidada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% dos debates iniciados com uma configuração válida e prompt informado concluem a etapa de preparação sem exigir correções manuais adicionais.
- **SC-002**: 100% das entradas interativas inválidas para quantidade de agentes ou rodadas são rejeitadas antes do início do debate, com orientação clara para nova tentativa.
- **SC-003**: Em debates executados sem `--output`, o usuário consegue identificar corretamente agente e rodada em todas as respostas exibidas no terminal.
- **SC-004**: 100% dos fluxos interativos bem-sucedidos geram um arquivo `debate.json` reutilizável ao final da coleta de configuração.
- **SC-005**: O usuário consegue concluir a configuração interativa inicial de um novo debate em até 3 minutos usando apenas o terminal.

## Assumptions

- O usuário já possui credenciais e ambiente aptos para executar outros comandos existentes do CLI.
- O formato de configuração seguirá um objeto JSON com chaves por agente e, para cada uma, campos de modelo e prompt.
- O prompt principal do debate será fornecido explicitamente pelo usuário no momento da execução, em vez de ser persistido dentro do arquivo `debate.json`.
- O arquivo `debate.json` gerado interativamente será salvo no diretório corrente de execução do comando.
- A conclusão final sempre será gerada após a última rodada, mesmo quando ocorrerem falhas parciais em respostas individuais, desde que o sistema ainda tenha material suficiente para encerrar o debate.

## Documentation Impact *(mandatory)*

- **docs/features.md**: adicionar a feature `debate`, incluindo modos por arquivo, variável de ambiente e fluxo interativo.
- **docs/code-map.md**: atualizar o mapa com o novo comando de CLI e os serviços ou fluxos adicionados para debate e conclusão.
- **docs/arquitetura.md**: registrar a ampliação do CLI de comandos simples para orquestração multiagente por rodadas.
- **docs/modelo-dados.md**: criar ou atualizar somente se o projeto passar a documentar formalmente a estrutura de configuração e resultado do debate.
- **docs/integracoes.md**: registrar o uso ampliado da integração externa para múltiplas execuções por rodada e geração de conclusão final.
- **docs/licoes-aprendidas.md**: registrar incidentes ou limitações encontrados na validação de entradas, exibição incremental e gravação de resultados.
- **docs/adr/**: nenhum ADR é assumido como obrigatório neste momento; criar apenas se a implementação exigir uma decisão estrutural nova para orquestração multiagente.
