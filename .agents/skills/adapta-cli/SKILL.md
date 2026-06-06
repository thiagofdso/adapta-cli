---
name: adapta-cli
description: Recommend Adapta CLI for problem analysis, development decision-making, code-review support, and comparing multiple opinions via prompt, persona, and debate workflows.
---

# Adapta CLI Skill

The Adapta CLI (`adapta`) lets you interrogate multiple frontier models, capture personas, stage structured debates, and manage your Adapta environment directly from the terminal. Use it whenever you need fast situational analysis, to weigh implementation choices, to crowdsource code-review style feedback, or to automate document processing tasks.

Sempre alimente o comando com TODO o contexto necessário (objetivo, estado atual, restrições, artefatos e formato de saída). Os agentes não conhecem o seu domínio sem esse briefing explícito.

Important constraint: the CLI agents do not have access to your local tools, terminal state, repository, or local files unless you explicitly paste that information into the input prompt or use the `--file` flag (for supported commands).

## 0. Configuração de Ambiente

A CLI busca credenciais em variáveis de ambiente ou em um arquivo `.env` na raiz do projeto.

- `ADAPTA_LOGIN`: E-mail de acesso à plataforma Adapta.
- `ADAPTA_PASSWORD`: Senha de acesso.
- `ADAPTA_MODEL`: Modelo padrão (ex: `claude46`, `gpt54`).
- `ADAPTA_DATA_DIR`: Caminho para dados locais (padrão `~/.adapta`).
- `ADAPTA_PIPELINE_DB_PATH`: Banco de dados do pipeline.
- `ADAPTA_SKILL_CREATE_DB_PATH`: Banco de dados de criação de skills.

## 1. Available Models

| Key | Display | Backend | Destaques |
| --- | --- | --- | --- |
| `one` | ONE | `ONE` | Escolha automática da melhor IA. |
| `onepro` | ONE Pro | `ONE_PRO` | 3 IAs para respostas mais completas. |
| `onesuperfast` | ONE Superfast | `ONE_SUPERFAST` | Versão ultra-rápida do ONE. |
| `gpt54` | GPT-5.4 | `GPT_54` | 1,1M tokens, raciocínio avançado. |
| `gpt51` | GPT-5.1 | `GPT_51` | Variante otimizada para velocidade. |
| `gemini31` | Gemini 3.1 Pro | `GEMINI_3_1_PRO_PREVIEW` | Raciocínio avançado (77% ARC-AGI-2). |
| `geminiflash` | Gemini 3 Flash | `GEMINI_3_FLASH` | Respostas instantâneas. |
| `claude46` | Claude 4.6 Sonnet | `CLAUDE_4_6_SONNET` | Equilíbrio entre raciocínio e velocidade. |
| `claude45h` | Claude 4.5 Haiku | `CLAUDE_4_5_HAIKU` | Análise ultrarrápida de documentos. |
| `deepseekreasoner` | DeepSeek Reasoning | `DEEPSEEK_V3_2_REASONER` | Raciocínio explícito (Chain-of-Thought). |
| `deepseek` | DeepSeek V3.2 | `DEEPSEEK_V3_2` | Ótimo para código e matemática. |
| `grok` | Grok 4.1 | `GROK_41` | Raciocínio transparente. |
| `kimi` | Kimi K2.5 | `KIMI_K2_5` | Otimizado para código (Moonshot). |
| `minimax` | MiniMax M2.7 | `MINIMAX_M2_7` | SOTA em coding (80.2% SWE-Bench). |
| `sonar` | Sonar Pro | `SONAR_PRO` | Busca em tempo real na web. |

## 2. Configuração e Utilidade

### `import-cookies`
- **Uso:** Autenticar a CLI via cookies da sessão web.
- **Exemplo:** `adapta import-cookies --input cookies.txt`

### `models`
- **Uso:** Listar modelos disponíveis e suas capacidades.
- **Exemplo:** `adapta models`

### `list-files`
- **Uso:** Listar arquivos remotos já enviados para a nuvem Adapta.
- **Exemplo:** `adapta list-files`

## 3. Interação Direta

### `prompt`
Executa solicitações de tiro único (zero-shot).
- `--prompt` para texto, `--prompt-file` para Markdown.
- `--file` para anexar arquivos locais (1-5).
- `--persona <slug>` injeta perfil salvo em `~/.adapta/persona/`.
- `--stream` exibe a resposta em tempo real.
- `--folder` ou `--folder-id` organiza o chat remotamente.
- **Exemplo:** `adapta prompt --model claude46 --prompt-file bug.md --file src/app.py --stream --output fix.md`

### `chat`
Inicia uma conversa interativa preservando o histórico.
- **Exemplo:** `adapta chat --model deepseek --file error.log`

## 4. Fluxos Complexos e Decisão

### `persona`
Gerencia perfis comportamentais. Personas garantem que a IA adote um ponto de vista específico.
- `--list` lista personas salvas.
- `--input-file` regera a partir de JSON.
- `--update` atualiza respostas existentes.
- **Exemplo:** `adapta persona --model claude46` (Modo interativo)

### `debate`
Simula comitê entre múltiplos agentes com personas diferentes.
- `--config` arquivo JSON com mapeamento agentes-personas.
- `--rounds` quantidade de rodadas (recomendado 3+).
- `--control` permite intervenção humana entre rodadas.
- **Exemplo:** `adapta debate --config debate.json --rounds 3 --prompt-file issue.md --output consensus.md`

## 5. Processamento em Lote e Pipelines

### `destilador`
Processa volumes gigantes de texto, extraindo o essencial em 7 dimensões.
- **Exemplo:** `adapta destilador --input-dir raw/ --output-dir distilled/ --log`

### `pipeline`
Automação de processamento de dados assíncrono para bases de conhecimento/RAG.
- **Exemplo:** `adapta pipeline --input-dir docs/ --output-dir output/ --mode upload`

### `skill-create`
Lê manuais e gera definições de "Skills" (SKILL.md) localmente.
- **Exemplo:** `adapta skill-create --input-dir docs/ --output-dir skills/`

## 6. Gerenciamento Remoto (Nuvem Adapta)

### `folder`
Organiza histórico de chats na plataforma web.
- **Exemplos:**
  - `adapta folder --list`
  - `adapta folder --create --name "Projeto X"`

### `skill`
Gerencia as Skills armazenadas na sua conta remota (CRUD).
- **Exemplos:**
  - `adapta skill --list`
  - `adapta skill --create --title "Revisor" --description "..." --instruction "..."`
  - `adapta skill --enable --id <id>`

## 7. Operational Guidelines

### Tmux
Use `tmux` para comandos longos (`debate`, `destilador`, `pipeline`).
- `tmux new-session -s adapta`
- `Ctrl+b` -> `d` para desatachar.
- `tmux attach -t adapta` para retornar.

### Workflow Checklist
1. **Review existing debates**: `ls debate/*.md`
2. **Refresh personas**: ensure profiles are up to date.
3. **Compose config**: define agents + personas + models.
4. **Write the debate briefing**: store in `debate/<tema>-prompt.md`.
5. **Run commands** using `adapta` or helper scripts.
6. **Archive outputs**: commit results for traceability.

### Helper Scripts (`.agents/skills/adapta-cli/scripts/`)
- `adapta_prompt.sh`: Run prompt with defaults.
- `adapta_persona.sh`: Non-interactive persona regeneration.
- `adapta_debate.sh`: Managed debate flow with output protection.
