# Graph Report - .  (2026-06-09)

## Corpus Check
- Corpus is ~37,419 words - fits in a single context window. You may not need a graph.

## Summary
- 411 nodes · 1209 edges · 13 communities
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 216 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Adapta API Client|Adapta API Client]]
- [[_COMMUNITY_Skill Creation Service|Skill Creation Service]]
- [[_COMMUNITY_Authentication Client|Authentication Client]]
- [[_COMMUNITY_CLI Commands|CLI Commands]]
- [[_COMMUNITY_Pipeline Service|Pipeline Service]]
- [[_COMMUNITY_Chat Debate Service|Chat Debate Service]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Knowledge Skill Prompts|Knowledge Skill Prompts]]
- [[_COMMUNITY_Persona Service|Persona Service]]
- [[_COMMUNITY_Book Implementation Prompts|Book Implementation Prompts]]
- [[_COMMUNITY_Logging Configuration|Logging Configuration]]
- [[_COMMUNITY_Strategic Insight Prompts|Strategic Insight Prompts]]

## God Nodes (most connected - your core abstractions)
1. `Any` - 44 edges
2. `AdaptaAuthenticator` - 29 edges
3. `AdaptaConversationClient` - 26 edges
4. `AdaptaClientAdapter` - 24 edges
5. `prompt()` - 20 edges
6. `Any` - 20 edges
7. `Settings` - 19 edges
8. `_run_stage1_for_folder()` - 19 edges
9. `Path` - 18 edges
10. `_run_stage1_for_folder()` - 18 edges

## Surprising Connections (you probably didn't know these)
- `Settings` --uses--> `Settings`  [INFERRED]
  src/adapta/config.py → src/adapta/models.py
- `ChatSession` --uses--> `ChatSession`  [INFERRED]
  src/adapta/services/chat_service.py → src/adapta/models.py
- `Path` --uses--> `DebateAgentConfig`  [INFERRED]
  src/adapta/cli.py → src/adapta/models.py
- `Path` --uses--> `DebateTurn`  [INFERRED]
  src/adapta/cli.py → src/adapta/models.py
- `Path` --uses--> `DebateControlDecision`  [INFERRED]
  src/adapta/cli.py → src/adapta/services/debate_service.py

## Import Cycles
- 1-file cycle: `src/adapta/services/__init__.py -> src/adapta/services/__init__.py`

## Hyperedges (group relationships)
- **Sete Dimensões de Análise de Livro** — livro_dimensao1_framework_completo_de_implementacao, livro_dimensao2_insights_revolucionarios, livro_dimensao3_aspectos_contra_intuitivos, livro_dimensao4_historias_e_casos_transformadores, livro_dimensao5_numeros_e_formulas_exatas, livro_dimensao6_aplicacoes_imediatas_pos_leitura, livro_dimensao7_citacoes_estrategicas_e_mantras [INFERRED 0.95]
- **Fluxo de Extração e Criação de Conhecimento** — pipeline_knowledge_extraction_indice_de_conhecimentos, pipeline_knowledge_extraction_plain_indice_de_conhecimentos_inline, pipeline_knowledge_creation_criacao_de_markdown_de_conhecimento, pipeline_knowledge_creation_plain_criacao_de_markdown_de_conhecimento_inline [INFERRED 0.95]
- **Fluxo de Extração e Criação de Skills** — pipeline_skill_extraction_plain_indice_de_skills, pipeline_skill_creation_plain_criacao_de_skill_md, pipeline_skill_extraction_plain_criterios_de_extracao_de_skills, pipeline_skill_creation_plain_estrutura_markdown_skill [INFERRED 0.95]

## Communities (13 total, 0 thin omitted)

### Community 0 - "Adapta API Client"
Cohesion: 0.10
Nodes (7): AdaptaClientAdapter, AdaptaConversationClient, ChatPayloadBuilder, extract_answer_text(), _first_non_none(), _generate_uuid7_like(), Any

### Community 1 - "Skill Creation Service"
Cohesion: 0.12
Nodes (54): SkillCreateRequest, SkillCreateRunResult, SkillDocument, _append_inline_blocks(), _build_creation_prompt(), _build_extraction_prompt(), _build_inline_text_block(), _build_skill_correction_prompt() (+46 more)

### Community 2 - "Authentication Client"
Cohesion: 0.09
Nodes (20): AdaptaAuthenticator, AdaptaHttpSession, AuthResult, ChatCompletionResult, create_client(), _extract_session_id_from_cookies(), import_cookies_to_session_cache(), _normalize_cookie_payload() (+12 more)

### Community 3 - "CLI Commands"
Cohesion: 0.12
Nodes (45): chat(), _collect_persona_answers(), _confirm_overwrite(), debate(), destilador(), _fail(), folder(), import_cookies() (+37 more)

### Community 4 - "Pipeline Service"
Cohesion: 0.13
Nodes (47): PipelineDocument, PipelineRequest, PipelineRunResult, PipelineDocument, PipelineRequest, PipelineRunResult, _build_creation_prompt(), _build_extraction_prompt() (+39 more)

### Community 5 - "Chat Debate Service"
Cohesion: 0.15
Nodes (39): DebateAgentConfig, DebateConfig, DebateResult, DebateRound, DebateTurn, ChatSession, DebateConfig, DebateControlDecision (+31 more)

### Community 6 - "Domain Models"
Cohesion: 0.13
Nodes (37): ChatSession, DistillationArtifact, DistillationDimension, DistillationInputItem, DistillationRequest, DistillationResult, ModelOption, PipelineArtifact (+29 more)

### Community 7 - "Knowledge Skill Prompts"
Cohesion: 0.14
Nodes (18): Casos de Fracasso Instrutivos, Casos de Sucesso, História Pessoal do Autor, Histórias e Casos Transformadores, Criação de Markdown de Conhecimento, Estrutura Markdown Conhecimento, Criação de Markdown de Conhecimento Inline, Texto Inline (+10 more)

### Community 8 - "Persona Service"
Cohesion: 0.25
Nodes (16): Service layer for Adapta CLI., build_persona_prompt(), build_persona_questionnaire(), extract_persona_content(), generate_persona_document(), get_persona_directory(), load_persona_questionnaire_from_file(), normalize_persona_name() (+8 more)

### Community 9 - "Book Implementation Prompts"
Cohesion: 0.12
Nodes (17): Arquitetura Conceitual, Ferramentas Práticas, Framework Completo de Implementação, Métricas e KPIs, Sistema de Implementação, Fórmulas e Equações, Métricas Mencionadas, Números e Fórmulas Exatas (+9 more)

### Community 10 - "Logging Configuration"
Cohesion: 0.53
Nodes (5): apply_current_backend_logging(), _configure_backend_logging(), configure_logging(), resolve_log_level(), Path

### Community 11 - "Strategic Insight Prompts"
Cohesion: 0.33
Nodes (6): Conhecimento Contra Consenso, Insights Revolucionários, Meta Insight, Aspectos Contra Intuitivos, Paradoxos Estratégicos, Senso Comum Realidade Evidência Implicação

## Knowledge Gaps
- **21 isolated node(s):** `Path`, `PipelineArtifact`, `Arquitetura Conceitual`, `Sistema de Implementação`, `Ferramentas Práticas` (+16 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Settings` connect `Authentication Client` to `Adapta API Client`, `CLI Commands`, `Domain Models`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `AdaptaAuthenticator` connect `Authentication Client` to `Adapta API Client`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `AdaptaClientAdapter` connect `Adapta API Client` to `Authentication Client`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `RuntimeError` (e.g. with `_distill_single_item()` and `extract_persona_content()`) actually correct?**
  _`RuntimeError` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Path`, `PipelineArtifact`, `Service layer for Adapta CLI.` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Adapta API Client` be split into smaller, more focused modules?**
  _Cohesion score 0.10303030303030303 - nodes in this community are weakly interconnected._
- **Should `Skill Creation Service` be split into smaller, more focused modules?**
  _Cohesion score 0.1164983164983165 - nodes in this community are weakly interconnected._