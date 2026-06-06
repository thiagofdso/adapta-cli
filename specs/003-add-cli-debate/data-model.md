# Data Model: Debate no CLI

## DebateAgentConfig

- **Purpose**: representar a configuração declarativa de um agente participante.
- **Fields**:
  - `agent_id`: identificador textual estável, como `A1` ou `Agent 1`
  - `model_key`: chave curta do modelo selecionado
  - `prompt`: instruções específicas do agente
- **Validation Rules**:
  - `agent_id` deve ser único dentro do debate
  - `model_key` deve existir no registro de modelos
  - `prompt` não pode ser vazio após normalização

## DebateConfig

- **Purpose**: representar a configuração completa necessária para iniciar o debate.
- **Fields**:
  - `agents`: lista ordenada de `DebateAgentConfig`
  - `rounds`: número total de rodadas
  - `topic_prompt`: problema ou tema debatido
  - `conclusion_model_key`: modelo responsável pela conclusão final
  - `output_path`: caminho opcional para persistência do resultado
  - `config_source`: origem efetiva da configuração, como argumento, ambiente ou interação
- **Validation Rules**:
  - `agents` deve conter pelo menos 2 itens
  - `rounds` deve ser inteiro maior que zero
  - `topic_prompt` não pode ser vazio
  - `conclusion_model_key` deve ser válido; quando ausente, assume `gemini`

## DebateAgentSession

- **Purpose**: associar a configuração do agente à sua sessão conversacional ativa durante o debate.
- **Fields**:
  - `agent`: `DebateAgentConfig`
  - `chat_id`: identificador remoto do chat
  - `messages`: histórico acumulado da sessão
  - `cleanup_required`: indicador de limpeza remota pendente
- **Validation Rules**:
  - cada agente deve manter sua própria sessão independente
  - `messages` deve preservar ordem cronológica

## DebateTurn

- **Purpose**: representar uma resposta individual de um agente em uma rodada específica.
- **Fields**:
  - `round_number`: número da rodada
  - `agent_id`: identificador do agente
  - `model_key`: modelo efetivamente usado no turno
  - `prompt_sent`: prompt consolidado enviado ao agente
  - `response_text`: resposta retornada ou mensagem de erro normalizada
  - `status`: sucesso, vazio ou erro
- **Validation Rules**:
  - `round_number` deve estar entre `1` e `rounds`
  - deve existir no máximo um turno por agente em cada rodada
  - `status` deve refletir o resultado do turno

## DebateRound

- **Purpose**: agrupar todos os turnos concluídos em uma mesma rodada.
- **Fields**:
  - `round_number`: identificador da rodada
  - `turns`: coleção ordenada de `DebateTurn`
- **Validation Rules**:
  - `turns` deve conter um item por agente configurado
  - a ordem de exibição deve ser determinística para facilitar leitura e testes

## DebateResult

- **Purpose**: representar o artefato final retornado ou salvo pela execução do debate.
- **Fields**:
  - `config`: `DebateConfig` efetiva usada na execução
  - `rounds`: coleção de `DebateRound`
  - `final_conclusion`: conclusão consolidada
  - `saved_path`: caminho opcional do arquivo salvo
  - `cleanup_warnings`: avisos gerados durante a remoção de chats remotos
- **Validation Rules**:
  - `final_conclusion` deve existir quando o debate encerrar com sucesso operacional
  - `saved_path` só deve existir quando `output_path` tiver sido informado
  - `cleanup_warnings` não invalida um resultado de debate já concluído

## State Transitions

```text
configurado -> validado -> rodando_rodada_1 -> ... -> rodando_rodada_n -> concluindo -> finalizado
                                      \-> falha_de_validacao
                                      \-> finalizado_com_avisos
```

- `configurado -> validado`: ocorre após resolver origem da configuração e validar agentes, rodadas e prompt.
- `validado -> rodando_rodada_n`: ocorre quando as sessões de cada agente são inicializadas e os turnos passam a ser executados.
- `rodando_rodada_n -> concluindo`: ocorre após a última rodada válida.
- `concluindo -> finalizado`: ocorre após gerar a conclusão e opcionalmente salvar a saída.
- `finalizado -> finalizado_com_avisos`: ocorre quando o debate termina, mas há avisos de cleanup remoto.
