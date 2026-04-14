# Arquitetura

## Estilo arquitetural

Projeto único em Python, empacotado como CLI e organizado em camadas leves de comando, serviços e integração externa.

## Componentes principais

- CLI Typer para `prompt`, `chat`, `models`, `list-files`, `debate`, `persona`, `destilador` e `pipeline`
- módulo de configuração baseado em `.env`
- registro de modelos para mapear aliases curtos para nomes do backend Adapta
- cliente HTTP assíncrono interno reestruturado em camadas de sessão, autenticação, upload/exclusão de arquivos e conversas
- serviços separados para prompt, chat, debate, persona, destilador, pipeline e persistência de saída

## Comunicação entre componentes

- comandos de CLI recebem opções, resolvem configuração, validam anexos opcionais e delegam para serviços
- serviços orquestram chamadas ao cliente Adapta e retornam respostas normalizadas
- o cliente encapsula autenticação, envio de prompts e exclusão de chats em classes com objetivos específicos
- no debate, cada agente mantém uma sessão de chat própria por toda a execução, pode incorporar opcionalmente o conteúdo de um arquivo de persona ao seu prompt, e a conclusão final é gerada a partir das respostas acumuladas das rodadas
- no comando `persona`, a CLI coleta respostas interativas, também pode ler respostas de `--input-file` ou reabrir uma persona com `--update`, resolve o modelo padrão ou um `--model` explícito pelo registro interno, gera um único markdown em chat efêmero e salva o resultado junto do JSON de respostas em uma pasta sob o diretório home real do usuário
- no destilador, a CLI internaliza o pipeline em 7 dimensões, carrega prompts especializados de `src/adapta/prompts/livro/` e usa upload de arquivo para gerar um consolidado por item
- no pipeline, a CLI internaliza um fluxo de extração e escrita de conhecimentos por diretório, usa prompts especializados em `src/adapta/prompts/pipeline/`, persiste estado operacional em SQLite local e grava índices e documentos dentro do diretório de saída informado

## Tecnologias

- Python 3.11
- Typer
- httpx
- pydantic-settings
- python-dotenv
- pytest

## Trade-offs conhecidos

- a CLI privilegia simplicidade e um único processo por sessão
- logs são opt-in para manter saída limpa no uso comum
- chat é efêmero: a sessão remota é excluída ao final por requisito do produto
- debate reutiliza o mesmo princípio de efemeridade do chat, mas com múltiplas sessões remotas por execução
- persona reutiliza o princípio de efemeridade do chat em uma única sessão remota e grava o resultado em arquivo local persistente
- destilador reutiliza o padrão de limpeza best-effort para uploads e artefatos remotos após a consolidação final
- no modo `--input` com `--output-dir`, o destilador preserva os arquivos parciais por dimensão para inspeção local
- pipeline reutiliza SQLite local para rastrear jobs e conhecimentos, evitando dependência de serviço externo para estado operacional
- a implementação atual internaliza apenas o subconjunto necessário do cliente do Adapta para prompt, chat e limpeza remota, reduzindo dependências externas do projeto
