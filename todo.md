# Backlog Adapta CLI – Brainstorm orientado a personas

## Funcionalidades atuais (referência rápida)
- `adapta prompt`: envio direto de prompts com anexos e exportação opcional.
- `adapta persona`: questionário guiado que grava respostas em `~/.adapta/persona/<slug>.json` e o prompt final em `~/.adapta/persona/<slug>.md`.
- `adapta debate`: orquestra múltiplos agentes/personas em rodadas, aceita anexos e salva conclusões com `--output`.
- Scripts de apoio (`.agents/skills/adapta-cli/scripts/`) para padronizar execuções e garantir saídas em `debate/`.

## Debate configurado
- Configuração: `debate/debate-cli-roadmap.json` (A1 Desenvolvedor Backend, A2 Engenheira Arquiteta, A3 Especialista em Linguagem).
- Personas-alvo residem em `~/.adapta/persona/` (JSON+MD). Execute `adapta debate --config debate/debate-cli-roadmap.json --rounds 3 --prompt "Panorama e roadmap da CLI" --output debate/<data>-roadmap.md` para coletar insights reais.

## Backlog priorizado (maior benefício → menor)

| # | Iniciativa | Descrição | Complexidade | Impacto | Notas |
|---|------------|-----------|--------------|---------|-------|
| 1 | `adapta debate init` | Gera boilerplate (personas sugeridas, config JSON e estrutura `debate/<slug>/`) e registra última execução para consulta rápida antes de um novo debate. | Média | Alta | Resolve dor do Arquiteta sobre governança e evita duplicar debates. |
| 2 | Biblioteca de personas reutilizáveis | Subcomando `adapta persona template --name <slug>` que cria JSON preenchido conforme o template oficial e opcionalmente sincroniza com `debate/people/`. | Baixa | Alta | Especialista em Linguagem pediu consistência dos perfis; facilita versionamento. |
| 3 | `adapta outputs list` | Lista debates e prompts já salvos (busca em `debate/` e `outputs/`), mostrando modelo, data e arquivo. | Média | Média/Alta | Desenvolvedor consegue verificar histórico antes de rodar novos prompts. |
| 4 | Plano de ação automático | Flag `adapta prompt --tasks` que transforma resposta em checklist (ex.: converte markdown em lista numerada + YAML). | Alta | Alta | Acelera follow-up pós-brainstorm; útil para code review/resolução de incidentes. |
| 5 | Cache de anexos | CLI lembra hash dos arquivos enviados e informa quando já existem no backend, oferecendo opção `--reuse`. | Média | Média | Reduz uploads repetidos, pedido recorrente do Desenvolvedor. |
| 6 | `adapta persona diff` | Compara duas versões de persona (JSON/MD) e destaca mudanças. | Baixa | Média | Ajuda governança/pessoas a documentar evolução das personas. |

## Próximos passos sugeridos
1. Rodar o debate com o arquivo recém-criado e arquivar a saída em `debate/` para enriquecer este backlog com evidências reais dos agentes.
2. Validar viabilidade de implementação #1 e #2 ainda nesta iteração (complexidade baixa/média e alto valor).
3. Usar `todo.md` como documento vivo; adicionar colunas de owner e status conforme iniciativas evoluam.
