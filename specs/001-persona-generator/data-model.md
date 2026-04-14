# Data Model: Persona Generator

## PersonaQuestionnaire

- **Purpose**: Representa as respostas coletadas durante a entrevista interativa.
- **Fields**:
  - `nome`
  - `cargo`
  - `setor`
  - `idade`
  - `tamanho_empresa`
  - `valores`
  - `comunicacao`
  - `senioridade`
  - `objetivo_6_12m`
  - `aspiracao_3_5a`
  - `dia_perfeito`
  - `dores`
  - `tira_sono`
  - `medos`
  - `forma_trabalho`
  - `inovacao`
  - `aprendizado`
  - `tom_voz`
  - `maneirismos`
  - `motiva_desmotiva`
- **Validation Rules**:
  - `nome` é obrigatório e não pode ser vazio ou conter apenas espaços.
  - `cargo` é obrigatório e não pode ser vazio ou conter apenas espaços.
  - Todos os demais campos podem ser vazios.
  - O nome precisa gerar um nome de arquivo seguro e determinístico.
- **Relationships**:
  - Alimenta um `PersonaPromptRequest`.

## PersonaPromptRequest

- **Purpose**: Representa a entrada enviada ao modelo para geração do markdown final.
- **Fields**:
  - `model_key`
  - `base_prompt`
  - `persona_json`
- **Validation Rules**:
  - `model_key` deve resolver para o modelo Claude pelo registro interno.
  - `base_prompt` é fixo para a feature e não pode ser vazio.
  - `persona_json` deve preservar campos vazios como strings vazias, sem preencher valores ausentes.
- **Relationships**:
  - É derivado de `PersonaQuestionnaire`.
  - Gera um `PersonaDocument`.

## PersonaDocument

- **Purpose**: Representa o markdown final salvo para reutilização futura.
- **Fields**:
  - `display_name`
  - `slug`
  - `output_path`
  - `content`
- **Validation Rules**:
- `output_path` deve apontar para a pasta de personas resolvida sob o diretório home real do usuário, equivalente ao caminho lógico `~/.adapta/persona/{slug}.md`.
  - `content` não pode ser vazio quando salvo como resultado final.
  - O salvamento depende de confirmação explícita caso o arquivo já exista.
- **Relationships**:
  - É produzido a partir de `PersonaPromptRequest`.

## PersonaGenerationResult

- **Purpose**: Resume o desfecho operacional do comando.
- **Fields**:
  - `questionnaire`
  - `document`
  - `overwrite_confirmed`
  - `saved`
  - `cleanup_warning`
- **Validation Rules**:
  - `saved` só pode ser verdadeiro quando o arquivo final foi gravado com conteúdo válido.
  - `cleanup_warning` é opcional e não invalida um sucesso de salvamento já concluído.
- **Relationships**:
  - Referencia `PersonaQuestionnaire` e `PersonaDocument`.

## State Transitions

### Questionnaire flow

`collecting` -> `validated` -> `submitted`

- Transição para `validated` exige `nome` e `cargo` válidos.
- Transição para `submitted` exige JSON pronto para envio ao modelo.

### Document flow

`draft` -> `ready_to_save` -> `saved`

- Transição para `ready_to_save` exige conteúdo gerado não vazio.
- Transição para `saved` exige destino resolvido, diretório disponível e confirmação de sobrescrita quando aplicável.

### Cleanup flow

`not_started` -> `attempted` -> `completed` ou `warned`

- A tentativa de cleanup ocorre sempre que uma conversa remota tiver sido aberta.
- `warned` indica falha de cleanup reportada ao usuário sem invalidar o artefato local.
