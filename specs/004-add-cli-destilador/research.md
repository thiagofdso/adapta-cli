# Research: Destilador no CLI

## Decision 1: Internalizar a lógica necessária do destilador no projeto

- **Decision**: Implementar no `adapta-cli` o subconjunto necessário do fluxo do destilador, sem importação ou execução de código a partir de `/mnt/c/whatsweb/adapta` em runtime.
- **Rationale**: O projeto já registra como lição obrigatória evitar dependência de código-fonte externo em tempo de execução. A nova funcionalidade precisa seguir o mesmo padrão de internalização usado no cliente do Adapta.
- **Alternatives considered**:
  - Importar o módulo externo diretamente: rejeitado por criar acoplamento estrutural fora do pacote distribuível.
  - Invocar o script externo como subprocesso: rejeitado por esconder dependência operacional e dificultar testes.

## Decision 2: Criar um serviço dedicado de destilação

- **Decision**: Colocar a orquestração do fluxo em `destilador_service`, mantendo `cli.py` responsável apenas pela interface do comando, validação superficial e mensagens ao usuário.
- **Rationale**: O CLI atual já segue o padrão comando fino + serviço, visto em `prompt_service`, `chat_service` e `debate_service`.
- **Alternatives considered**:
  - Implementar tudo no comando `destilador`: rejeitado por piorar testabilidade e consistência arquitetural.
  - Embutir a lógica em `client.py`: rejeitado por misturar transporte externo com orquestração de negócio.

## Decision 3: Suportar modo por arquivo e modo por diretório

- **Decision**: O comando aceitará tanto `--input` com `--output` quanto `--input-dir` com `--output-dir`, com validação explícita para impedir combinações ambíguas.
- **Rationale**: Isso preserva o formato já planejado por arquivo e também recupera o comportamento operacional do código original baseado em diretórios, mas agora com parâmetros explícitos.
- **Alternatives considered**:
  - Suportar apenas arquivo único: rejeitado porque perderia o comportamento desejado de diretório.
  - Suportar apenas diretórios: rejeitado porque removeria o formato já planejado e mais preciso.

## Decision 4: Preservar processamento por 7 dimensões com retries limitados

- **Decision**: O pipeline continuará gerando dimensões intermediárias antes da consolidação final, com repetição limitada quando uma dimensão não produzir resposta válida.
- **Rationale**: Esse é o comportamento funcional central do destilador existente e precisa ser mantido para preservar o valor do processo.
- **Alternatives considered**:
  - Fazer uma única chamada para consolidar tudo: rejeitado por alterar demais o comportamento esperado.
  - Exigir intervenção manual entre dimensões: rejeitado por piorar a automação do comando.

## Decision 5: Fazer limpeza local e remota em modo best-effort

- **Decision**: Limpeza de uploads temporários e artefatos remotos deve ocorrer ao final, sem transformar uma destilação já concluída em falha apenas por erro de limpeza.
- **Rationale**: O projeto já usa cleanup best-effort no chat e no debate; o mesmo padrão reduz vazamento operacional sem degradar a UX.
- **Alternatives considered**:
  - Falhar o comando após consolidar o resultado por erro de limpeza: rejeitado por piorar a experiência operacional.
  - Nunca limpar artefatos: rejeitado por aumentar custo operacional e acúmulo de resíduos temporários.

## Decision 6: Validar cedo arquivo de entrada e destino de saída

- **Decision**: Rejeitar antes do processamento qualquer entrada inexistente, ilegível, incompatível ou saída não gravável.
- **Rationale**: Isso economiza chamadas externas e mantém o padrão de mensagens curtas e acionáveis da CLI.
- **Alternatives considered**:
  - Deixar falhar apenas durante o processamento: rejeitado por desperdiçar tempo e custo operacional.
  - Tentar corrigir caminhos automaticamente: rejeitado por reduzir previsibilidade.

## Decision 7: Derivar saídas por item no modo por diretório

- **Decision**: No modo por diretório, o sistema gerará um arquivo final por item processado em `--output-dir`, usando convenção consistente de nome baseada no arquivo de entrada.
- **Rationale**: Isso preserva a semântica de lote do comportamento antigo e evita conflito entre múltiplos resultados em uma única execução.
- **Alternatives considered**:
  - Gerar um único consolidado para todo o diretório: rejeitado por alterar demais o comportamento esperado do destilador.
  - Exigir que o usuário informe um arquivo de saída por item: rejeitado por tornar o modo em lote pouco prático.

## Decision 8: Listar arquivos remotos antes do upload

- **Decision**: O cliente deve consultar `/api/files/v2` antes de subir um novo arquivo e reaproveitar o artefato remoto quando já existir um item com o mesmo nome.
- **Rationale**: Isso reduz uploads redundantes, acelera execuções repetidas e mantém o comportamento operacional observável via um comando dedicado de listagem.
- **Alternatives considered**:
  - Sempre reenviar o arquivo: rejeitado por desperdiçar chamadas remotas e criar duplicação operacional.
  - Deduplicar por hash local: rejeitado neste estágio por exigir contrato adicional não confirmado no backend.

## Decision 9: Reutilizar a infraestrutura de arquivo em comandos conversacionais

- **Decision**: A mesma infraestrutura de listagem, upload e normalização de metadados deve ser usada em `prompt`, `chat`, `debate` e `destilador`, com `--file` limitado a 1-5 anexos por comando.
- **Rationale**: O comportamento fica consistente entre comandos e mantém a lógica de upload centralizada no client e nos serviços.
- **Alternatives considered**:
  - Implementar anexos separadamente em cada comando: rejeitado por duplicar regras e aumentar risco de divergência.
  - Restringir anexos apenas ao destilador: rejeitado porque outros fluxos conversacionais também se beneficiam do mesmo contrato.
