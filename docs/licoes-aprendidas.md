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
