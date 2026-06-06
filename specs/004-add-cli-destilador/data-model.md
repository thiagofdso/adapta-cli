# Data Model: Destilador no CLI

## DistillationRequest

- **Purpose**: representar uma execução individual do comando `destilador`.
- **Fields**:
  - `input_path`: caminho absoluto ou relativo do arquivo de entrada individual
  - `input_dir_path`: caminho absoluto ou relativo do diretório de entrada em lote
  - `output_path`: caminho absoluto ou relativo do arquivo consolidado final
  - `output_dir_path`: caminho absoluto ou relativo do diretório de saída em lote
  - `mode`: arquivo ou diretório
  - `auto_confirm`: indicador para consolidação automática quando aplicável
  - `upload_delay_seconds`: atraso operacional entre upload e processamento remoto
- **Validation Rules**:
  - `mode` deve ser consistente com a combinação de parâmetros informada
  - `input_path` deve apontar para um arquivo existente e legível quando `mode` for arquivo
  - `input_dir_path` deve apontar para um diretório existente quando `mode` for diretório
  - `output_path` deve apontar para um arquivo gravável ou sobrescrevível quando `mode` for arquivo
  - `output_dir_path` deve apontar para um diretório utilizável quando `mode` for diretório
  - `upload_delay_seconds` deve ser maior ou igual a zero

## DistillationInputItem

- **Purpose**: representar um item individual resolvido para processamento, inclusive dentro de um lote por diretório.
- **Fields**:
  - `source_path`: arquivo efetivamente processado
  - `target_output_path`: arquivo consolidado correspondente
  - `source_origin`: argumento de arquivo único ou item derivado de diretório
- **Validation Rules**:
  - cada `source_path` deve ser único dentro da mesma execução
  - `target_output_path` deve ser determinístico para o item

## DistillationDimension

- **Purpose**: representar uma dimensão individual do pipeline de destilação.
- **Fields**:
  - `dimension_number`: identificador da dimensão
  - `prompt_text`: instrução usada para gerar a dimensão
  - `attempt_count`: quantidade de tentativas realizadas
  - `selected_content`: conteúdo escolhido para a dimensão
  - `status`: sucesso, erro, preservado ou pendente
- **Validation Rules**:
  - `dimension_number` deve estar entre 1 e 7
  - `selected_content` só pode estar vazio quando `status` não for sucesso

## DistillationArtifact

- **Purpose**: representar um artefato local ou remoto criado durante a execução.
- **Fields**:
  - `artifact_type`: upload remoto, arquivo temporário local, dimensão parcial ou consolidado final
  - `path_or_identifier`: caminho local ou identificador remoto
  - `cleanup_required`: indicador de limpeza pendente
  - `preserved_reason`: motivo para preservação quando não houver limpeza
- **Validation Rules**:
  - artefatos remotos devem registrar identificador suficiente para exclusão
  - `preserved_reason` deve existir quando `cleanup_required` for falso por falha ou interrupção

## RemoteFileEntry

- **Purpose**: representar um arquivo remoto retornado pela listagem da conta no Adapta.
- **Fields**:
  - `filename`: nome do arquivo remoto
  - `path`: identificador ou caminho remoto usado para referência e limpeza
  - `mediaType`: tipo de mídia informado pelo backend
  - `size`: tamanho do arquivo em bytes quando disponível
  - `url`: URL assinada ou URL remota quando disponível
- **Validation Rules**:
  - `filename` deve existir para permitir deduplicação por nome
  - `path` deve existir quando o backend devolver identificador utilizável para limpeza
  - a normalização deve aceitar variantes equivalentes de payload retornadas pela API

## PromptRequest

- **Purpose**: representar uma execução do comando `prompt`, com origem textual e anexos opcionais.
- **Fields**:
  - `model_key`: alias de modelo resolvido
  - `prompt_text`: prompt final enviado ao modelo
  - `prompt_source`: origem inline ou arquivo local de prompt
  - `output_path`: caminho opcional para persistência
  - `file_paths`: lista opcional de anexos locais a subir antes da chamada
- **Validation Rules**:
  - `prompt_source` deve apontar para uma única origem de prompt por execução
  - `file_paths` deve conter entre 0 e 5 itens válidos

## DebateConfig

- **Purpose**: representar uma execução do comando `debate`, incluindo anexos opcionais compartilhados entre rodadas.
- **Fields**:
  - `agents`: agentes participantes
  - `rounds`: quantidade de rodadas
  - `topic_prompt`: tema principal do debate
  - `conclusion_model_key`: modelo da conclusão final
  - `output_path`: caminho opcional de persistência
  - `config_source`: origem da configuração
  - `file_paths`: anexos locais opcionais reutilizados por todos os agentes e rodadas
- **Validation Rules**:
  - `file_paths` deve conter entre 0 e 5 itens válidos
  - os anexos devem ser enviados uma única vez e reutilizados em todas as rodadas da execução

## DistillationResult

- **Purpose**: representar o resultado final da execução do destilador.
- **Fields**:
  - `request`: `DistillationRequest` efetiva
  - `processed_items`: coleção de `DistillationInputItem`
  - `dimensions`: coleção ordenada de `DistillationDimension`
  - `final_output_paths`: caminhos finais gravados
  - `cleanup_warnings`: avisos gerados na limpeza
  - `preserved_artifacts`: artefatos mantidos para análise
- **Validation Rules**:
  - `final_output_paths` só deve existir quando a destilação concluir com sucesso
  - `dimensions` deve preservar ordem determinística
  - `cleanup_warnings` não invalida uma execução já concluída

## State Transitions

```text
recebido -> validado -> upload_concluido -> dimensoes_em_execucao -> consolidado -> finalizado
        \-> falha_de_validacao
        \-> interrompido_com_preservacao
        \-> falha_com_preservacao
```

- `recebido -> validado`: ocorre após validar entrada e saída.
- `validado -> upload_concluido`: ocorre após subir ou preparar o artefato necessário para processamento remoto.
- `upload_concluido -> dimensoes_em_execucao`: ocorre quando a geração das 7 dimensões inicia.
- `dimensoes_em_execucao -> consolidado`: ocorre após selecionar conteúdo válido para todas as dimensões necessárias.
- `consolidado -> finalizado`: ocorre após gravar o arquivo final e concluir a limpeza bem-sucedida ou com avisos.
- `* -> interrompido_com_preservacao` e `* -> falha_com_preservacao`: ocorrem quando a execução precisa manter artefatos intermediários para análise.

## Shared File Flow

```text
arquivo_local -> validado -> listagem_remota -> reutilizado_ou_upload -> anexado_ao_fluxo -> limpeza_ou_reuso
```

- `validado -> listagem_remota`: ocorre antes do upload quando o fluxo depende de anexos remotos.
- `listagem_remota -> reutilizado_ou_upload`: ocorre quando o cliente encontra um arquivo com mesmo nome ou decide subir um novo artefato.
- `reutilizado_ou_upload -> anexado_ao_fluxo`: ocorre quando os metadados normalizados do arquivo passam a ser usados em `prompt`, `chat`, `debate` ou `destilador`.
