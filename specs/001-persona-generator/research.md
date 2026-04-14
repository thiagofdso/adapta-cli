# Research: Persona Generator

## Decision 1: Coletar respostas com prompts interativos pequenos na CLI

- **Decision**: Usar `typer.prompt` no comando para coletar as respostas por bloco, revalidando o nome imediatamente e delegando validações estruturais adicionais para o serviço de persona.
- **Rationale**: O repositório já usa a CLI para experiência interativa e re-prompt de erros recuperáveis, enquanto os serviços mantêm validações reutilizáveis e mensagens amigáveis.
- **Alternatives considered**:
  - Concentrar toda validação na CLI: rejeitado por duplicar regras e quebrar o padrão atual.
  - Fazer a entrevista fora do comando, com configuração em arquivo: rejeitado porque a feature pede fluxo guiado no terminal.
- **References**: `src/adapta/cli.py`, `src/adapta/services/prompt_service.py`, `tests/unit/test_cli.py`, `tests/unit/test_prompt_service.py`

## Decision 2: Salvar a persona em diretório do usuário resolvido de forma multiplataforma

- **Decision**: Resolver o diretório de destino padrão a partir da API de diretório home da linguagem, sem depender de `~` literal, e persistir o markdown final na pasta lógica `~/.adapta/persona/{nome-persona}.md`, criando a pasta quando necessário.
- **Rationale**: O projeto já usa o diretório home para estado local persistente e essa abordagem preserva compatibilidade com Linux e Windows sem assumir expansão textual ou separadores fixos.
- **Alternatives considered**:
  - Salvar no diretório atual: rejeitado porque diverge do requisito e do padrão de estado local do projeto.
  - Gravar o arquivo diretamente dentro da CLI sem helper compartilhado: rejeitado por duplicar comportamento de persistência já centralizado.
- **References**: `src/adapta/config.py`, `src/adapta/services/output_service.py`, `src/adapta/services/pipeline_service.py`, `tests/integration/test_output_file_command.py`

## Decision 3: Fixar o modelo lógico em `claude` via registro interno

- **Decision**: Resolver o modelo da feature com a chave lógica `claude` pelo `registry`, sem expor `--model`, sem seleção interativa e sem herdar `ADAPTA_MODEL`.
- **Rationale**: O requisito pede explicitamente Claude e o repositório já possui a chave `claude` mapeada para o backend canônico. Isso mantém a escolha consistente com outros fluxos que fixam Claude internamente.
- **Alternatives considered**:
  - Reutilizar o fluxo genérico de escolha de modelo: rejeitado porque permitiria modelos diferentes do exigido.
  - Gravar diretamente o identificador do backend no novo serviço: rejeitado por ignorar o registry como fonte de verdade.
- **References**: `src/adapta/registry.py`, `src/adapta/cli.py`, `src/adapta/config.py`, `src/adapta/services/destilador_service.py`, `src/adapta/services/pipeline_service.py`

## Decision 4: Usar conversa efêmera com cleanup best-effort

- **Decision**: Construir a geração em torno de um fluxo remoto efêmero com cleanup em `finally`, preservando o arquivo local salvo quando a limpeza da conversa falhar.
- **Rationale**: O repositório já trata sessões temporárias como efêmeras e rebaixa falhas de cleanup para aviso operacional quando o resultado principal já foi entregue ao usuário.
- **Alternatives considered**:
  - Confiar em cleanup manual posterior: rejeitado porque contraria o requisito e os padrões de chat efêmero.
  - Falhar o comando inteiro se o cleanup falhar: rejeitado porque esconderia um resultado válido já salvo localmente.
- **References**: `src/adapta/services/prompt_service.py`, `src/adapta/services/chat_service.py`, `src/adapta/services/debate_service.py`, `src/adapta/client.py`, `tests/integration/test_chat_cleanup.py`

## Decision 5: Manter mensagens de erro curtas e acionáveis

- **Decision**: Continuar usando mensagens de erro curtas no comando, com falhas esperadas convertidas para saída amigável sem traceback verboso.
- **Rationale**: Esse é o padrão de UX vigente na CLI e já possui cobertura de testes para erros operacionais previsíveis.
- **Alternatives considered**:
  - Expor traceback completo ao usuário: rejeitado por piorar a experiência de CLI em erros esperados.
  - Capturar exceções genéricas demais e ocultar contexto importante: rejeitado por dificultar diagnóstico e divergir do padrão atual.
- **References**: `src/adapta/cli.py`, `tests/unit/test_cli.py`, `docs/licoes-aprendidas.md`
