# Research: Debate no CLI

## Decision 1: Criar um serviço dedicado de debate

- **Decision**: Implementar a orquestração do debate em `debate_service`, deixando `cli.py` responsável apenas por opções, prompts interativos e tratamento final de erros.
- **Rationale**: O projeto já separa parsing de linha de comando e orquestração em serviços específicos. Isso mantém consistência com `prompt_service` e `chat_service`, reduz acoplamento e facilita TDD.
- **Alternatives considered**:
  - Concentrar toda a lógica no comando `debate`: mais rápido inicialmente, mas inconsistente com a arquitetura vigente.
  - Mover a lógica para `client.py`: incorreto para a camada, que deve continuar focada em transporte e autenticação.

## Decision 2: Reutilizar uma sessão de chat por agente durante todo o debate

- **Decision**: Cada agente manterá uma sessão de chat própria ao longo de todas as rodadas, acumulando contexto local e remoto até a conclusão.
- **Rationale**: O fluxo atual de chat já preserva contexto por `chat_id` e histórico de mensagens. Isso corresponde naturalmente à memória individual de cada agente entre rodadas.
- **Alternatives considered**:
  - Criar um chat novo por rodada: simplifica isolamento, mas perde contexto e aumenta overhead de cleanup.
  - Compartilhar um único chat entre todos os agentes: reduz separação de papéis e embaralha o histórico.

## Decision 3: Tratar configuração em três fontes com precedência explícita

- **Decision**: Resolver a configuração de agentes na ordem `--config`, `ADAPTA_DEBATE_CONFIG`, fluxo interativo com gravação em `debate.json`.
- **Rationale**: A ordem atende à especificação e segue o padrão já usado pela CLI para escolha de parâmetros explícitos, ambiente e fallback interativo.
- **Alternatives considered**:
  - Priorizar variável de ambiente sobre parâmetro: contraria a expectativa do usuário para a linha de comando.
  - Exigir sempre arquivo de configuração: reduziria usabilidade e conflitaria com a necessidade de onboarding interativo.

## Decision 4: Validar entradas com mensagens curtas e acionáveis

- **Decision**: Reutilizar o padrão de `ValueError` ou `RuntimeError` convertido em mensagem curta em stderr e saída com código `1`.
- **Rationale**: O repositório já padronizou esse comportamento para evitar traceback em erros esperados de CLI.
- **Alternatives considered**:
  - Deixar exceções subirem até o Typer: introduz saída verbosa e inconsistência de UX.
  - Adicionar modo interativo permissivo com correções implícitas: dificulta previsibilidade e teste.

## Decision 5: Exibir incrementalmente apenas no modo sem arquivo de saída

- **Decision**: Quando `--output` não for informado, cada resposta concluída será impressa imediatamente no terminal com cabeçalho identificando agente e rodada; quando `--output` existir, o sistema gravará o resultado completo no arquivo indicado e poderá manter a saída de terminal reduzida ao essencial.
- **Rationale**: A especificação exige visibilidade incremental no terminal apenas no fluxo sem gravação, preservando uma saída limpa quando o objetivo principal for persistência.
- **Alternatives considered**:
  - Sempre exibir tudo e também salvar em arquivo: duplicaria saída em casos automatizados.
  - Somente gravar em arquivo sem nenhuma mensagem de status: reduziria observabilidade operacional.

## Decision 6: Registrar um artefato final completo do debate

- **Decision**: Consolidar um resultado final contendo configuração efetiva, respostas por rodada, conclusão final e caminho opcional de arquivo salvo.
- **Rationale**: O debate envolve múltiplos turnos e múltiplos agentes; um artefato agregado facilita persistência, testes e inspeção posterior.
- **Alternatives considered**:
  - Tratar apenas strings soltas por rodada: torna persistência e testes de integração menos estáveis.
  - Persistir somente a conclusão final: perderia contexto útil do debate.

## Decision 7: Fazer cleanup remoto best-effort ao final

- **Decision**: Todos os chats remotos abertos pelo debate serão rastreados e encerrados em uma etapa final best-effort, sem invalidar um debate já concluído por falha de cleanup.
- **Rationale**: O comando `chat` já estabelece o princípio de sessão efêmera com aviso em stderr se a limpeza falhar. O debate deve preservar o mesmo comportamento operacional.
- **Alternatives considered**:
  - Falhar o comando após debate bem-sucedido por cleanup parcial: piora a experiência do usuário.
  - Ignorar cleanup: contraria a arquitetura e aumenta risco de recursos remotos órfãos.
