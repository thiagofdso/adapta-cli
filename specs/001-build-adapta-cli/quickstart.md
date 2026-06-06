# Quickstart: Build Adapta CLI

## 1. Preparar o projeto

1. Criar `pyproject.toml` com entry point `adapta`.
2. Criar o pacote `src/adapta` e a estrutura de testes em `tests/unit` e `tests/integration`.
3. Criar `Makefile` com alvos para testes, prompt e chat.
4. Criar `scripts/install-local.sh` e `scripts/install-remote.sh` para disponibilizar o comando `adapta` no sistema.
5. Copiar o arquivo `.env` existente de `/mnt/c/whatsweb/adapta/.env` para a raiz de `/mnt/c/whatsweb/adapta-cli` sem alterar os nomes das variáveis obrigatórias.

## 2. Executar doc-first com TDD na ordem pedida

1. Criar ou atualizar a documentação negocial e técnica obrigatória em `docs/` antes de criar testes ou código.
2. Escrever testes unitários para configuração, resolução de modelo, validação de argumentos, leitura de prompt, escrita de saída, configuração de logs, scripts de instalação, `Makefile` e limpeza de chat.
3. Executar a suíte unitária e confirmar falha inicial.
4. Implementar apenas o mínimo necessário para a suíte unitária ficar verde.
5. Refatorar mantendo a suíte verde.
6. Só então escrever os testes de integração da CLI real.

## 3. Rodar testes unitários

```bash
pytest tests/unit
```

## 4. Rodar testes de integração

Pré-condições:
- `.env` presente na raiz do projeto CLI
- credenciais válidas carregadas
- ambiente com acesso ao serviço Adapta

```bash
pytest tests/integration
```

## 5. Cenários mínimos de integração

1. Prompt inline:

```bash
adapta prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"
```

Resultado esperado: saída `2`.

2. Prompt por arquivo:

```bash
adapta prompt --model gpt --prompt-file prompt.txt
```

3. Prompt com arquivo de saída:

```bash
adapta prompt --model gpt --prompt "quanto é 1+1 responda somente o valor" --output saida.txt
```

4. Chat interativo:

```bash
adapta chat --model gpt
```

5. Prompt com comportamento padrão sem logs:

```bash
adapta prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"
```

6. Prompt com log mínimo:

```bash
adapta --log info prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"
```

7. Prompt com log detalhado:

```bash
adapta --log debug prompt --model gpt --prompt "quanto é 1+1 responda somente o valor"
```

8. Listagem de modelos:

```bash
adapta models
```

9. Instalação local:

```bash
./scripts/install-local.sh
```

10. Instalação global recomendada:

```bash
make install
```

Se `pipx` não estiver disponível no ambiente, o script tenta `python -m pipx` e, na ausência dele, cria uma `venv` dedicada em `~/.local/share/adapta-cli/venv` com link simbólico em `~/.local/bin/adapta`.

11. Instalação remota:

```bash
./scripts/install-remote.sh <repo-remoto>
```

12. Atalhos de execução:

```bash
make test
make prompt
make chat
make install
make install-local
make install-remote REMOTE_REPO=<repo-remoto>
```

## 6. Critérios de pronto para implementação

1. A documentação negocial e técnica obrigatória em `docs/` é atualizada antes dos testes e da implementação.
2. Todos os testes unitários passam antes da criação dos testes de integração.
3. Os testes de integração validam prompt inline, prompt por arquivo, saída em arquivo, listagem de modelos e limpeza do chat.
4. Os testes também validam ausência de logs por padrão, seleção de nível de log, scripts de instalação e `Makefile`.
5. O projeto instalado expõe o comando `adapta` no terminal a partir de origem local e remota.
6. O `Makefile` oferece ao menos `make test`, `make prompt`, `make chat`, `make install`, `make install-local` e `make install-remote`.
