# adapta-cli

CLI em Python para usar os modelos da Adapta no terminal.

## Requisitos

- Python 3.11+
- credenciais válidas em `.env`

Variáveis obrigatórias:

- `ADAPTA_LOGIN`
- `ADAPTA_PASSWORD`

Variável opcional:

- `ADAPTA_MODEL`

## Instalação

Instalação recomendada:

```bash
make install
```

Instalação local a partir do diretório atual:

```bash
./scripts/install-local.sh
```

Instalação remota:

```bash
./scripts/install-remote.sh <repo-remoto> [ref]
```

Os scripts tentam usar `pipx` primeiro, depois `python -m pipx` e, se necessário, criam uma `venv` dedicada em `~/.local/share/adapta-cli/venv` com link em `~/.local/bin/adapta`.

## Uso

Prompt inline:

```bash
adapta prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"
```

Prompt por arquivo:

```bash
adapta prompt --model gpt --prompt-file prompt.txt
```

Salvar saída em arquivo:

```bash
adapta prompt --model gpt --prompt "quanto é 1+1 responda somente o valor" --output saida.txt
```

Chat interativo:

```bash
adapta chat --model gpt
```

Listar modelos disponíveis:

```bash
adapta models
```

Logs são opt-in:

```bash
adapta --log info prompt --model gpt --prompt "teste"
adapta --log debug prompt --model gpt --prompt "teste"
```

Se `--model` não for informado, a CLI usa `ADAPTA_MODEL` ou pede seleção interativa.

## Makefile

```bash
make test
make prompt
make chat
make install
make install-local
make install-remote REMOTE_REPO=<repo-remoto>
```

## Desenvolvimento

Estrutura principal:

- `src/adapta/`
- `tests/unit/`
- `tests/integration/`
- `docs/`

Rodar testes unitários:

```bash
pytest tests/unit
```

Rodar testes de integração:

```bash
pytest tests/integration
```

Rodar teste real de paralelismo progressivo do GPT:

```bash
ADAPTA_RUN_PARALLEL_GPT_TESTS=1 ADAPTA_PARALLEL_GPT_START=3 ADAPTA_PARALLEL_GPT_STEP=3 ADAPTA_PARALLEL_GPT_MAX=30 .venv/bin/pytest -s tests/integration/test_gpt_parallel_limit.py
```

Documentação complementar:

- `docs/features.md`
- `docs/arquitetura.md`
- `docs/code-map.md`
- `docs/integracoes.md`

## Comportamento atual

- `prompt` aceita `--prompt`, `--prompt-file` e `--output`
- `chat` remove a sessão remota ao encerrar
- `models` lista os modelos suportados com chave, nome amigável e identificador do backend
- logs ficam desativados por padrão
- erros esperados da CLI retornam mensagem curta sem traceback verboso
