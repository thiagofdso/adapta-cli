# Licoes Aprendidas

## 2026-04-12 - Planejamento da CLI doc-first

### Problema

O fluxo inicial estava orientado apenas a TDD e não deixava explícita a documentação negocial e técnica antes da implementação.

### Causa

A necessidade de documentação mínima obrigatória foi formalizada depois do plano inicial.

### Solucao

Atualizar constituição, plano e tarefas para exigir doc-first antes de testes e código.

### ❌ NAO FAZER

- iniciar implementação sem atualizar `docs/`
- deixar decisões arquiteturais implícitas

### ✅ FAZER

- atualizar documentação funcional e técnica antes dos testes
- registrar decisões e erros relevantes durante a execução

## 2026-04-12 - Evitar dependência de código-fonte externo em runtime

### Problema

A primeira implementação da CLI tentou carregar o cliente do Adapta a partir de um diretório externo configurado por variável de ambiente.

### Causa

A solução buscava reaproveitar rapidamente o código existente, mas deixava a CLI dependente de outro repositório em tempo de execução.

### Solucao

Internalizar um cliente mínimo do Adapta e reestruturá-lo em classes menores para sessão HTTP, autenticação e conversas.

### ❌ NAO FAZER

- depender de código-fonte externo para rodar uma CLI distribuível
- esconder acoplamentos estruturais em variáveis de ambiente de desenvolvimento

### ✅ FAZER

- copiar apenas o comportamento necessário para dentro do projeto
- separar autenticação, sessão HTTP e chat em responsabilidades claras

## 2026-04-12 - Tratar ambientes com PEP 668 na instalação

### Problema

A instalação local falhou em ambientes com `externally-managed-environment`, impedindo o uso de `pip install --user` como estratégia genérica.

### Causa

O fluxo de instalação assumia que o Python do sistema aceitaria instalação direta no ambiente do usuário, o que não é garantido em distribuições com PEP 668 ativo.

### Solucao

Priorizar `pipx`, depois `python -m pipx` e, como fallback final, instalar em uma `venv` dedicada com link simbólico para o binário da CLI.

### ❌ NAO FAZER

- assumir que `pip install --user` sempre funciona em ambientes gerenciados pelo sistema
- depender de um único caminho de instalação para entregar o binário

### ✅ FAZER

- prever fallback para `venv` dedicada em scripts de instalação
- documentar claramente onde o binário será exposto e quando ajustar o `PATH`

## 2026-04-12 - Evitar traceback verboso para erros esperados de CLI

### Problema

Erros de validação e de execução previsíveis estavam aparecendo com traceback e saída verbosa demais para uso comum em terminal.

### Causa

O comportamento padrão do Typer favorece depuração, mas não combina com uma CLI voltada a uso direto por linha de comando em cenários de erro esperado.

### Solucao

Desativar `pretty_exceptions` e converter `ValueError` e `RuntimeError` em mensagens curtas com saída controlada e código de erro `1`.

### ❌ NAO FAZER

- expor stack trace para erros operacionais esperados da CLI
- misturar mensagem amigável ao usuário com saída de depuração por padrão

### ✅ FAZER

- retornar mensagens curtas e acionáveis em stderr
- manter detalhes de depuração restritos ao modo de log explícito
