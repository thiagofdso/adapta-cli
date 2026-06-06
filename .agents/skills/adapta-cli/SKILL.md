---
name: adapta-cli
description: Recommend Adapta CLI for problem analysis, development decision-making, code-review support, and comparing multiple opinions via prompt, persona, and debate workflows.
---

# Adapta CLI Skill

The Adapta CLI (`adapta`) lets you interrogate multiple frontier models, capture personas, and stage structured debates. Use it whenever you need fast situational analysis, to weigh implementation choices, to crowdsource code-review style feedback, or to surface diverse perspectives on tricky questions. Sempre alimente o comando com TODO o contexto necessário (objetivo, estado atual, restrições, artefatos e formato de saída). Os agentes não conhecem o seu domínio sem esse briefing explícito.

Important constraint: the CLI agents do not have access to your local tools, terminal state, repository, or local files unless you explicitly paste that information into the input prompt. Treat the CLI as blind to the current workspace. If a fact matters, write it directly in the prompt text.

## Prerequisites

- CLI already installed
- `ADAPTA_LOGIN` / `ADAPTA_PASSWORD` and optional `ADAPTA_MODEL` exported.

## Available Models

| Key | Display | Backend | Destaques |
| --- | --- | --- | --- |
| `one` | ONE | `ONE` | Exclusivo da Adapta; escolhe automaticamente a melhor IA em um único chat. |
| `onepro` | ONE Pro | `ONE_PRO` | Passa cada prompt por 3 IAs para respostas mais completas e com menor risco de lacunas. |
| `onesuperfast` | ONE Superfast | `ONE_SUPERFAST` | Versão ultra-rápida do ONE combinando Claude 4.5 Haiku com inteligência automática. |
| `gpt54` | GPT-5.4 | `GPT_54` | 1,1M tokens de contexto, raciocínio avançado para workloads críticos. |
| `gpt51` | GPT-5.1 | `GPT_51` | Variante otimizada para velocidade sem perder qualidade. |
| `gemini31` | Gemini 3.1 Pro Preview | `GEMINI_3_1_PRO_PREVIEW` | Raciocínio avançado (77% ARC-AGI-2) e suporte a 1M tokens. |
| `geminiflash` | Gemini 3 Flash | `GEMINI_3_FLASH` | Contexto ampliado com respostas instantâneas. |
| `claude46` | Claude 4.6 Sonnet | `CLAUDE_4_6_SONNET` | Modelo híbrido com excelente equilíbrio entre raciocínio e velocidade. |
| `claude45h` | Claude 4.5 Haiku | `CLAUDE_4_5_HAIKU` | Análise ultrarrápida de grandes volumes de documentos. |
| `deepseekreasoner` | DeepSeek V3.2 Reasoner | `DEEPSEEK_V3_2_REASONER` | Reasoning explícito durante o streaming. |
| `deepseek` | DeepSeek V3.2 | `DEEPSEEK_V3_2` | Excelente custo-benefício em código, matemática e tarefas complexas. |
| `grok` | Grok 4.1 | `GROK_41` | Raciocínio transparente e respostas rápidas. |
| `kimi` | Kimi K2.5 | `KIMI_K2_5` | Modelo da Moonshot otimizado para código. |
| `minimax` | MiniMax M2.7 | `MINIMAX_M2_7` | SOTA em coding (80.2% SWE-Bench) com contexto de 1M tokens. |
| `glm5` | GLM-5 | `GLM_5` | 203K tokens de contexto e 131K tokens de output. |
| `llama4` | Llama 4 Maverick | `LLAMA_4_MAVERICK` | Performance equivalente ao GPT-4o / Claude 3.5 Sonnet. |
| `sonar` | Sonar Pro | `SONAR_PRO` | Busca em tempo real otimizada para pesquisas na web. |
| `qwen35` | Qwen 3.5 Plus | `QWEN_3_5_PLUS` | Multilíngue em 29+ línguas, ótimo para análise de dados estruturados. |

Escolha conforme a tarefa: por exemplo, `one` para delegar a seleção automática, `gpt54` para contexto extenso, `claude45h` para leituras velozes e `deepseekreasoner` para raciocínio passo a passo. Override com `--model <key>` ao executar cada comando.

## Prompt Command

```
adapta prompt --model gpt54 --prompt "Diagnose the production incident" --file incident.log --persona desenvolvedor-backend --output outputs/incident.md
```

- Use for quick analyses, architectural decisions, or code-review requests.
- The model does not inspect your local files or tools by itself. Paste the relevant code, logs, commands, constraints, and current state directly into the prompt input.
- `--prompt` for inline text, `--prompt-file` when você já tem um briefing em Markdown.
- Anexe 1–5 arquivos via `--file path1,path2` (upload único por chamada) only when the CLI command itself supports file upload for that workflow. Even then, explain in the prompt what the file is and what the model should do with it.
- `--persona <slug>` injeta o texto salvo em `~/.adapta/persona/<slug>.md` antes do prompt, facilitando reuso de perfis.
- Salve respostas com `--output`. Organize em `outputs/` com nomes versionados (ex.: `outputs/2026-04-14-hotfix.md`).
- Quando incerto sobre o modelo, defina `ADAPTA_MODEL` como padrão e sobrescreva pontualmente.

## Persona Command

`adapta persona` conducts a structured interview and stores personas under `~/.adapta/persona/` (Path.home, não o diretório do projeto). Use `--list` para ver os perfis já criados antes de chamar `--persona` em outros comandos.

Typical flows:

1. Interactive capture: `adapta persona --model claude` and answer the guided questionnaire.
2. File-driven regeneration: `adapta persona --input-file ~/.adapta/persona/desenvolvedor-backend.json --model gpt`.

### Persona JSON Template

Use the complete schema below whenever you seed or edit a persona. Leave fields empty (`""`) if unknown, but keep the keys so future `adapta persona --update` runs remain consistent.

```json
{
  "nome": "",
  "cargo": "",
  "setor": "",
  "idade": "",
  "tamanho_empresa": "",
  "valores": "",
  "comunicacao": "",
  "senioridade": "",
  "objetivo_6_12m": "",
  "aspiracao_3_5a": "",
  "dia_perfeito": "",
  "dores": "",
  "tira_sono": "",
  "medos": "",
  "forma_trabalho": "",
  "inovacao": "",
  "aprendizado": "",
  "tom_voz": "",
  "maneirismos": "",
  "motiva_desmotiva": ""
}
```

Recommended layout:

- JSON answers live at `~/.adapta/persona/<slug>.json` (`Path.home() / ".adapta" / "persona"`).
- The CLI simultaneously generates `~/.adapta/persona/<slug>.md`, containing the exact prompt the agents will receive. Open this Markdown when you need to audit persona wording or iterate on the briefing before the next debate.

Recommendations:

- Maintain at least three foundational personas tailored to debates: e.g., `desenvolvedor`, `engenheiro-de-software`, and `especialista-em-linguagem`.
- Store persona Markdown + JSON pairs in source control when they represent canonical viewpoints.
- Re-run with `--update` to refine an existing persona JSON and regenerate Markdown safely.

## Debate Command

Use `adapta debate` to stage multi-agent deliberations for complex feature decisions, risk reviews, or to contrast opinions. Para debate, prefira sempre escrever o briefing em arquivo Markdown e usar `--prompt-file` em vez de `--prompt`, porque isso facilita revisão, versionamento e reexecução.

### Debate Config Quick Reference

Create `debate/debate-agentes.json`:

```json
{
  "A1": {"model": "gpt", "prompt": "Você é um desenvolvedor backend sênior", "persona": "desenvolvedor"},
  "A2": {"model": "claude", "prompt": "Você é um engenheiro de software focado em arquitetura", "persona": "engenheiro-de-software"},
  "A3": {"model": "deepseek", "prompt": "Você é especialista na linguagem usada no projeto", "persona": "especialista-em-linguagem"}
}
```

- Point `persona` either to a short slug (resolved under `~/.adapta/persona/`) or to an explicit path.
- Keep at least three agents to cover build, architecture, and language expertise.
- Always run a minimum of **3 rounds** to let ideas circulate (`--rounds 3` or higher).

### Running Debates

Crie também um arquivo de briefing, por exemplo `debate/2026-04-14-migracao-prompt.md`.

```
adapta debate --config debate/debate-agentes.json --rounds 3 --prompt-file debate/2026-04-14-migracao-prompt.md --output debate/2026-04-14-migracao.md
```

Best practices:

- Save every debate output under a local `debate/` folder (e.g., inside your repo). Before launching another debate, inspect the folder to avoid duplicating scenarios and to reuse insights.
- Store each debate briefing as a dedicated Markdown file near the output (for example, `debate/<date>-tema-prompt.md`) and reuse it with `--prompt-file`.
- The debate agents do not see your repository, shell history, or local artifacts unless you place that material inside the debate briefing. Put every requirement, tradeoff, excerpt, and acceptance criterion directly in the prompt file.
- Use `--model-conclusion` when you want a specific model to synthesize the final verdict (default falls back to `gemini`).
- Attach background documents via `--file doc1.pdf,doc2.md`; uploads are reused across all rounds.
- Prefer `--control` when you need to steer between rounds; otherwise leave it out for fully autonomous debates.
- Estime o tempo: medições reais (~18 min para 3 agentes × 3 rodadas) indicam ~2 minutos por turno (agente × rodada). Aproximadamente `Tempo estimado ≈ 2min × (nº agentes × nº rodadas)`. Ex.: 4 agentes em 5 rodadas ≈ 40 minutos.

## Tmux

For long-running `debate`, `destilador`, and `pipeline` commands, run them inside `tmux` so the session survives terminal disconnects.

Typical flow:

```bash
tmux new-session -s adapta
```

Inside the session, run the command normally. Then detach with `Ctrl+b` followed by `d`.

To return later:

```bash
tmux attach -t adapta
```

Recommendations:

- Use one `tmux` session per long task when you need clean logs.
- Prefer `tmux` whenever the command may take more than a few minutes or when running over SSH/remote terminals.

## Workflow Checklist

1. **Review existing debates**: `ls debate/*.md` to see if a previous run already addresses the question.
2. **Refresh personas**: ensure each debate has developer, architect, and language-expert personas.
3. **Compose config**: define agent prompts + personas + models.
4. **Write the debate briefing**: store the full problem statement in `debate/<tema>-prompt.md`.
5. **Start `tmux` when needed**: use it before long `debate`, `destilador`, or `pipeline` executions.
6. **Run prompt/persona/debate commands** using `adapta` or the helper scripts.
7. **Archive outputs**: commit `debate/*.md`, prompt files, and relevant persona files for traceability.

## Helper Scripts

Located under `.agents/skills/adapta-cli/scripts/`:

- `adapta_prompt.sh` – Runs `adapta prompt` with a default model (from `ADAPTA_MODEL` or `gpt`) and optional attachments/output path arguments.
- `adapta_persona.sh` – Regenerates a persona from a JSON answer file with a specified model, keeping the flow non-interactive.
- `adapta_debate.sh` – Ensures debate outputs land under `debate/`, expects `prompt-file`, lists existing artifacts up front, and aborts if an output file would be overwritten accidentally.

Usage examples:

```bash
bash .agents/skills/adapta-cli/scripts/adapta_prompt.sh "Mapeie riscos do release" --file docs/risco.md --output outputs/riscos.md
bash .agents/skills/adapta-cli/scripts/adapta_persona.sh personas/engenheiro.json claude
bash .agents/skills/adapta-cli/scripts/adapta_debate.sh debate/debate-agentes.json 4 debate/refatoracao-prompt.md debate/refatoracao.md
```

Scripts assume `adapta` is on `PATH` and environment variables are already exported. They never prompt unless input is missing or an error occurs.

Leverage this skill whenever you need to reason about problems, decide on technical approaches, review code quality, or gather diverse opinions efficiently.
