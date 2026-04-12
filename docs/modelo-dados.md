# Modelo de Dados

## Entidades principais

### Settings

- `adapta_login`
- `adapta_password`
- `adapta_model`
- `env_file_path`

Regra: login e senha são obrigatórios para chamadas reais.

### ModelOption

- `key`
- `display_name`
- `backend_name`
- `supports_chat`

Regra: `key` deve ser único e mapear para um modelo válido do backend.

### PromptRequest

- `model_key`
- `prompt_text`
- `prompt_source`
- `output_path`

Regra: apenas uma origem de prompt por execução.

### ChatSession

- `chat_id`
- `model_key`
- `messages`
- `cleanup_required`

Regra: o chat remoto deve ser excluído ao final da sessão.
