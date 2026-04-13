# Licoes Aprendidas

## 2026-04-12 - Planejamento da CLI doc-first

### Problema

O fluxo inicial estava orientado apenas a TDD e não deixava explícita a documentação negocial e técnica antes da implementação.

### Causa

A necessidade de documentação mínima obrigatória foi formalizada depois do plano inicial.

### Solucao

Atualizar constituição, plano e tarefas para exigir doc-first antes de testes e código.

### ❌ NAO FAZER

- iniciar implementação sem atualizar `docs/`
- deixar decisões arquiteturais implícitas

### ✅ FAZER

- atualizar documentação funcional e técnica antes dos testes
- registrar decisões e erros relevantes durante a execução

## 2026-04-12 - Evitar dependência de código-fonte externo em runtime

### Problema

A primeira implementação da CLI tentou carregar o cliente do Adapta a partir de um diretório externo configurado por variável de ambiente.

### Causa

A solução buscava reaproveitar rapidamente o código existente, mas deixava a CLI dependente de outro repositório em tempo de execução.

### Solucao

Internalizar um cliente mínimo do Adapta e reestruturá-lo em classes menores para sessão HTTP, autenticação e conversas.

### ❌ NAO FAZER

- depender de código-fonte externo para rodar uma CLI distribuível
- esconder acoplamentos estruturais em variáveis de ambiente de desenvolvimento

### ✅ FAZER

- copiar apenas o comportamento necessário para dentro do projeto
- separar autenticação, sessão HTTP e chat em responsabilidades claras

## 2026-04-12 - Tratar ambientes com PEP 668 na instalação

### Problema

A instalação local falhou em ambientes com `externally-managed-environment`, impedindo o uso de `pip install --user` como estratégia genérica.

### Causa

O fluxo de instalação assumia que o Python do sistema aceitaria instalação direta no ambiente do usuário, o que não é garantido em distribuições com PEP 668 ativo.

### Solucao

Priorizar `pipx`, depois `python -m pipx` e, como fallback final, instalar em uma `venv` dedicada com link simbólico para o binário da CLI.

### ❌ NAO FAZER

- assumir que `pip install --user` sempre funciona em ambientes gerenciados pelo sistema
- depender de um único caminho de instalação para entregar o binário

### ✅ FAZER

- prever fallback para `venv` dedicada em scripts de instalação
- documentar claramente onde o binário será exposto e quando ajustar o `PATH`

## 2026-04-12 - Evitar traceback verboso para erros esperados de CLI

### Problema

Erros de validação e de execução previsíveis estavam aparecendo com traceback e saída verbosa demais para uso comum em terminal.

### Causa

O comportamento padrão do Typer favorece depuração, mas não combina com uma CLI voltada a uso direto por linha de comando em cenários de erro esperado.

### Solucao

Desativar `pretty_exceptions` e converter `ValueError` e `RuntimeError` em mensagens curtas com saída controlada e código de erro `1`.

### ❌ NAO FAZER

- expor stack trace para erros operacionais esperados da CLI
- misturar mensagem amigável ao usuário com saída de depuração por padrão

### ✅ FAZER

- retornar mensagens curtas e acionáveis em stderr
- manter detalhes de depuração restritos ao modo de log explícito

## 2026-04-12 - Reproduzir contratos de arquivo a partir do HAR em fatias pequenas

### Problema

Era necessário implementar a listagem remota de arquivos sem acesso estável ao corpo completo das respostas do navegador.

### Causa

O `har.json` era grande e algumas entradas não traziam `response.content.text`, o que inviabiliza assumir o payload inteiro de uma vez.

### Solucao

Inspecionar o HAR com `jq` em partes pequenas para confirmar endpoint, paginação e headers essenciais, e então implementar o parser do cliente de forma tolerante a formatos equivalentes (`data`, `files`, `items`, `results`).

### ❌ NAO FAZER

- presumir o contrato completo da listagem sem validar o HAR
- acoplar o parser a um único formato rígido quando o backend já mostra variações de campos

### ✅ FAZER

- analisar o HAR por endpoint e metadados antes de codificar
- normalizar os metadados de arquivo no client antes de comparar ou reutilizar uploads

## 2026-04-12 - Centralizar a validação de anexos de CLI

### Problema

`prompt` e `chat` passaram a aceitar anexos opcionais via `--file`, ambos com o mesmo limite e as mesmas validações básicas.

### Causa

A regra de negócio é compartilhada: aceitar de 1 a 5 arquivos existentes, separados por vírgula, e falhar cedo em caso de entrada inválida.

### Solucao

Centralizar a normalização de `Path` em um helper reutilizado pela CLI e pelo fluxo de prompt, mantendo a lógica de upload no serviço que efetivamente faz a chamada ao backend.

### ❌ NAO FAZER

- duplicar manualmente o parsing de anexos em cada comando
- deixar a validação apenas no nível HTTP, depois de abrir a sessão remota

### ✅ FAZER

- validar contagem e existência dos arquivos antes de iniciar o fluxo remoto
- reutilizar o mesmo conjunto de anexos durante a sessão de chat quando o comando for iniciado com `--file`

## 2026-04-12 - Fazer upload único para anexos compartilhados no debate

### Problema

No debate, os mesmos anexos precisam estar disponíveis para múltiplos agentes e múltiplas rodadas.

### Causa

Se o upload acontecer dentro de cada mensagem, o fluxo repete trabalho remoto e pode multiplicar arquivos equivalentes sem necessidade.

### Solucao

Realizar o upload uma única vez no início do `run_debate` e reutilizar os metadados retornados em todas as chamadas `chat_with_files` dos agentes.

### ❌ NAO FAZER

- repetir o upload dos mesmos anexos a cada rodada ou agente
- espalhar a lógica de reutilização de anexos entre CLI e serviço

### ✅ FAZER

- manter o upload compartilhado centralizado no serviço de debate
- passar os arquivos já normalizados para o fluxo de chat das rodadas

## 2026-04-12 - Reaproveitar capacidades internas via comandos pequenos de CLI

### Problema

A CLI já sabia listar arquivos remotos no client, mas esse comportamento não estava exposto diretamente para inspeção operacional.

### Causa

A capacidade foi implementada primeiro como detalhe interno de deduplicação de upload.

### Solucao

Adicionar um comando pequeno e direto, `list-files`, reaproveitando o mesmo método do client e mantendo a saída tabulada simples para uso manual.

### ❌ NAO FAZER

- duplicar chamadas HTTP só para criar um comando novo
- esconder uma capacidade útil apenas como detalhe interno de outro fluxo

### ✅ FAZER

- expor o método já existente no client por um comando dedicado
- manter formato de saída simples e estável para inspeção rápida

## 2026-04-13 - Internalizar pipeline legado sem importar o outro repositório

### Problema

O novo comando `pipeline` precisava reaproveitar o comportamento do fluxo legado sem transformar a CLI em um wrapper dependente de outro checkout em runtime.

### Causa

A implementação original mistura prompts, SQLite, uploads e lógica de estágios em um módulo grande com dependências locais que não existem neste projeto.

### Solucao

Internalizar apenas o contrato observável necessário: descoberta recursiva, índices JSON, markdowns por conhecimento, SQLite local e prompts copiados para `src/adapta/prompts/pipeline/`.

### ❌ NAO FAZER

- importar `pipeline.py` de outro repositório em tempo de execução
- esconder dependência externa atrás de variável de ambiente de caminho

### ✅ FAZER

- copiar apenas prompts e regras necessárias
- manter a orquestração dentro de `src/adapta/services/pipeline_service.py`
