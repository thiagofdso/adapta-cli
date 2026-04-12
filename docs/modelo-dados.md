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

### DebateAgentConfig

- `agent_id`
- `model_key`
- `prompt`

Regra: cada agente precisa de identificador único, modelo válido e prompt não vazio.

### DebateConfig

- `agents`
- `rounds`
- `topic_prompt`
- `conclusion_model_key`
- `output_path`
- `config_source`

Regra: o debate exige pelo menos 2 agentes e pelo menos 1 rodada.

### DebateTurn

- `round_number`
- `agent_id`
- `model_key`
- `prompt_sent`
- `response_text`
- `status`

Regra: deve existir no máximo um turno por agente em cada rodada.

### DebateRound

- `round_number`
- `turns`

Regra: a rodada agrega as respostas de todos os agentes configurados.

### DebateResult

- `config`
- `rounds`
- `final_conclusion`
- `saved_path`
- `cleanup_warnings`

Regra: a conclusão final é produzida após a última rodada e avisos de cleanup não invalidam o resultado já concluído.
