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
- `file_paths`

Regra: apenas uma origem de prompt por execução e no máximo 5 anexos locais por chamada.

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
- `file_paths`

Regra: o debate exige pelo menos 2 agentes, pelo menos 1 rodada e reutiliza o mesmo conjunto opcional de anexos em todas as rodadas.

### RemoteFileEntry

- `filename`
- `path`
- `mediaType`
- `size`
- `url`

Regra: `filename` deve existir para permitir deduplicação de upload e inspeção via `list-files`.

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

### DistillationRequest

- `input_path`
- `input_dir_path`
- `output_path`
- `output_dir_path`
- `mode`
- `upload_delay_seconds`

Regra: o modo por arquivo exige `input_path` e `output_path`; o modo por diretório exige `input_dir_path` e `output_dir_path`.

Observação: `input_path` com `output_dir_path` é permitido e produz um consolidado único dentro do diretório de saída, preservando os parciais por dimensão.

### DistillationInputItem

- `source_path`
- `target_output_path`
- `source_origin`

Regra: cada item resolvido para processamento deve apontar para uma origem única e um destino determinístico.

Observação: `source_origin` distingue fluxos como `input`, `input-output-dir` e `input-dir` para decidir se os arquivos parciais devem ser preservados.

### DistillationDimension

- `dimension_number`
- `prompt_text`
- `attempt_count`
- `selected_content`
- `status`

Regra: cada dimensão precisa manter no máximo uma saída final por item processado.

### DistillationArtifact

- `artifact_type`
- `path_or_identifier`
- `cleanup_required`
- `preserved_reason`

Regra: artefatos temporários e remotos devem ser rastreáveis para limpeza ou preservação.

Exemplos: upload remoto do PDF, subdiretório local com `dimensao1.txt` a `dimensao7.txt`, consolidado final `.md`.

### DistillationResult

- `request`
- `processed_items`
- `dimensions`
- `final_output_paths`
- `cleanup_warnings`
- `preserved_artifacts`

Regra: a execução pode produzir um consolidado por item e avisos de cleanup não invalidam sucesso já concluído.

Observação: quando o usuário escolhe `--output-dir` com `--input`, os artefatos parciais do item permanecem disponíveis para inspeção local mesmo após o consolidado final ser salvo.

### PipelineRequest

- `input_dir_path`
- `output_dir_path`
- `db_path`
- `mode`
- `job_filter`
- `keep_chat`
- `log_enabled`

Regra: `input_dir_path` e `output_dir_path` são obrigatórios; `db_path` segue precedência entre opção explícita, ambiente e padrão local.

### PipelineRunResult

- `input_dir_path`
- `output_dir_path`
- `db_path`
- `processed_files`
- `index_paths`
- `generated_documents`
- `cleanup_warnings`

Regra: a execução precisa informar os artefatos produzidos e avisos de limpeza sem invalidar sucesso já concluído.

### PipelineJobRecord

- `id`
- `file_path`
- `file_name`
- `folder_path`
- `stage_id`
- `status_id`
- `created_at`

Regra: cada arquivo elegível deve gerar no máximo um job por banco e manter rastreamento por pasta de origem.

### PipelineKnowledgeRecord

- `id`
- `name`
- `description`
- `position`
- `folder_path`
- `status_id`
- `created_at`
- `files`

Regra: cada conhecimento precisa manter lista única de arquivos associados, limitada ao escopo funcional do pipeline legado.
