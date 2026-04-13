# Research: Comando pipeline por diretório

## Decision 1: Internalizar o pipeline legado como serviço local da CLI

- **Decision**: Implementar o comando `pipeline` como um novo comando Typer e um serviço interno da CLI, reaproveitando o comportamento observável do pipeline legado sem importar `/mnt/c/whatsweb/adapta` em runtime.
- **Rationale**: O repositório já formalizou que a CLI não deve depender de código-fonte externo em execução. O pipeline legado depende de módulos e infraestrutura que não existem dentro deste projeto distribuível. A abordagem mais alinhada é a já usada pelo `destilador`: internalizar apenas o subconjunto necessário do fluxo.
- **Alternatives considered**:
  - Importar diretamente `pipeline.py` do outro repositório: rejeitado por acoplamento externo em runtime.
  - Executar o pipeline legado por subprocesso: rejeitado pelo mesmo acoplamento e por dificultar teste e empacotamento.
  - Copiar integralmente a implementação legada: rejeitado por excesso de acoplamento técnico e baixa aderência ao princípio de solução mínima.

## Decision 2: Preservar contrato funcional de entrada e saída do pipeline original

- **Decision**: Manter compatibilidade funcional com o pipeline original para formatos aceitos, varredura recursiva de diretórios, artefatos de índice e artefatos documentais, apenas tornando configuráveis `input-dir`, `output-dir` e o banco local.
- **Rationale**: O pedido do usuário exige explicitamente o mesmo formato de entrada e saída. Isso reduz risco operacional para quem já conhece o pipeline original e evita retrabalho de adaptação de arquivos e processos.
- **Alternatives considered**:
  - Simplificar o fluxo e produzir apenas um artefato final agregado: rejeitado por quebrar a compatibilidade pedida.
  - Alterar o layout de saída para um novo padrão exclusivo da CLI: rejeitado por aumentar custo de migração sem necessidade.

## Decision 3: Usar SQLite local com precedência determinística de configuração

- **Decision**: Usar SQLite local semelhante ao original, com resolução de caminho nesta ordem: `--db-path` > `ADAPTA_PIPELINE_DB_PATH` > caminho padrão documentado.
- **Rationale**: O projeto já usa precedência explícita entre opção de CLI e ambiente em outros fluxos. O parâmetro explícito deve vencer por previsibilidade operacional e testabilidade. SQLite mantém paridade com o pipeline original e evita introduzir serviço externo.
- **Alternatives considered**:
  - Aceitar apenas variável de ambiente: rejeitado por reduzir controle por execução.
  - Aceitar apenas parâmetro de CLI: rejeitado por dificultar configuração persistente em automações.
  - Persistir em arquivos JSON soltos: rejeitado por perder similaridade operacional com o pipeline original.

## Decision 4: Adotar caminho padrão de banco fora do diretório de trabalho

- **Decision**: Definir como padrão um caminho local estável e específico do usuário, em `~/.local/state/adapta-cli/pipeline.db`.
- **Rationale**: O banco representa estado operacional, não artefato de saída. Mantê-lo fora do diretório corrente evita criação acidental de bancos em locais arbitrários e funciona melhor para uma CLI instalada.
- **Alternatives considered**:
  - Criar o banco no diretório atual: rejeitado por comportamento imprevisível.
  - Criar o banco dentro de `output-dir`: rejeitado por misturar estado operacional com resultados da execução.
  - Criar o banco na raiz do repositório: rejeitado por não servir bem a instalações fora do checkout.

## Decision 5: Documentar o contrato do comando em Markdown orientado a comportamento

- **Decision**: Criar `contracts/pipeline-command.md` em formato Markdown, com sintaxe do comando, opções, ambiente, ordem de resolução, regras de validação e garantias operacionais.
- **Rationale**: Esse é o padrão já adotado nas specs de `debate` e `destilador`, e cobre melhor comportamento de CLI, mensagens, precedência e efeitos em filesystem do que um schema mais rígido.
- **Alternatives considered**:
  - Contrato mínimo só com flags: rejeitado por não capturar precedência e validações.
  - Schema JSON/YAML do comando: rejeitado por divergir do padrão do repositório.

## Decision 6: Planejar ADR para a internalização do pipeline com persistência local

- **Decision**: Registrar um novo ADR durante a implementação para justificar a internalização do pipeline legado com persistência SQLite local configurável.
- **Rationale**: A constituição exige ADR quando houver decisão arquitetural ou trade-off relevante. Aqui há uma decisão explícita entre reaproveitar comportamento legado e evitar dependência externa em runtime, além da escolha de persistência local.
- **Alternatives considered**:
  - Não registrar ADR: rejeitado por deixar implícita uma decisão arquitetural provavelmente questionável no futuro.
