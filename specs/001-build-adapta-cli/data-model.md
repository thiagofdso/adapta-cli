# Data Model: Build Adapta CLI

## ModelOption

- Purpose: Representa um modelo disponível para uso na CLI.
- Fields:
- `key`: identificador curto aceito na CLI, como `gpt`, `o3` ou `claude`
- `display_name`: nome legível mostrado em listas interativas
- `backend_name`: nome real enviado ao backend do Adapta, como `GPT_5`
- `supports_chat`: indica se o modelo pode ser usado no fluxo de chat
- Validation Rules:
- `key` deve ser único e estável
- `backend_name` deve mapear para um modelo existente no Adapta

## Settings

- Purpose: Reúne a configuração de autenticação e comportamento padrão da CLI.
- Fields:
- `adapta_login`: login obrigatório para autenticação
- `adapta_password`: senha obrigatória para autenticação
- `adapta_model`: modelo padrão opcional
- `env_file_path`: caminho efetivo do `.env` carregado
- Validation Rules:
- `adapta_login` e `adapta_password` são obrigatórios para chamadas reais
- `adapta_model`, quando informado, deve existir no registro de modelos aceitos

## ExecutionOptions

- Purpose: Representa opções transitórias passadas por linha de comando para uma execução específica.
- Fields:
- `log_level`: nível de log solicitado para a execução quando a pessoa optar por ativar logs
- Validation Rules:
- `log_level` deve estar entre os níveis suportados pela CLI
- ausência de `log_level` significa execução sem logs operacionais

## InstallationSource

- Purpose: Representa a origem usada para instalar a CLI como comando do sistema.
- Fields:
- `kind`: tipo de origem, `local` ou `remote`
- `location`: caminho local ou URL do repositório remoto
- `target_command`: nome do executável esperado após a instalação
- Validation Rules:
- `kind` deve ser um dos tipos suportados
- `location` deve estar presente e ser compatível com o tipo escolhido
- `target_command` deve ser `adapta`

## MakeTarget

- Purpose: Representa um atalho operacional exposto pelo `Makefile`.
- Fields:
- `name`: nome do alvo, como `test`, `prompt` ou `chat`
- `purpose`: objetivo principal do alvo
- `required_inputs`: variáveis opcionais ou obrigatórias aceitas na chamada do `make`
- Validation Rules:
- `name` deve ser único no `Makefile`
- alvos de execução devem encaminhar para a CLI oficial do projeto

## PromptRequest

- Purpose: Representa uma execução única de prompt.
- Fields:
- `model_key`: modelo solicitado ou resolvido por padrão
- `prompt_text`: conteúdo final enviado ao backend
- `prompt_source`: origem do conteúdo, `inline` ou `file`
- `output_path`: caminho opcional para persistência da resposta
- Validation Rules:
- exatamente uma origem de prompt deve ser informada
- `prompt_text` não pode ser vazio após normalização
- `output_path`, quando informado, deve apontar para local gravável

## ChatSession

- Purpose: Mantém o estado de uma conversa temporária com o backend.
- Fields:
- `chat_id`: identificador único da conversa
- `model_key`: modelo selecionado para a sessão
- `messages`: histórico ordenado de mensagens de usuário e assistente
- `cleanup_required`: indica se a sessão remota precisa ser removida ao finalizar
- State Transitions:
- `initialized` -> `active` quando a primeira mensagem é enviada
- `active` -> `closing` quando a pessoa encerra o chat ou ocorre erro fatal
- `closing` -> `deleted` quando a exclusão remota é concluída
- `closing` -> `cleanup_failed` quando a exclusão remota falha e a CLI precisa avisar a pessoa usuária

## ResponseArtifact

- Purpose: Representa o resultado textual devolvido ao usuário.
- Fields:
- `text`: resposta principal retornada pelo modelo
- `destination`: `stdout`, arquivo ou ambos
- `saved_path`: caminho do arquivo gravado, quando existir
- Validation Rules:
- `text` deve estar presente para considerar a execução bem-sucedida
- `saved_path` só pode existir quando a gravação for concluída com sucesso

## Relationships

- `Settings` influencia a resolução de `ModelOption` padrão.
- `ExecutionOptions` influencia a configuração de logging da execução.
- `InstallationSource` influencia o fluxo de instalação e disponibilização do comando no sistema.
- `MakeTarget` influencia a ergonomia local para testes e execução manual.
- `PromptRequest` usa exatamente um `ModelOption`.
- `ChatSession` usa exatamente um `ModelOption` e acumula múltiplas mensagens.
- `ResponseArtifact` é produzido por `PromptRequest` ou por cada turno de `ChatSession`.
