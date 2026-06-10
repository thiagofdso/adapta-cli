---
name: adapta-cli-commands
description: Guia completo de todos os comandos disponíveis na Adapta CLI, ensinando como e para que usar cada um no dia a dia de desenvolvimento e análise.
---

# Adapta CLI - Guia Completo de Comandos

A Adapta CLI (`adapta`) possui diversos comandos organizados em categorias: configuração, interação direta, fluxos complexos, processamento em lote e gerenciamento remoto na plataforma Adapta.

---

## 0. Configuração de Ambiente

Antes de usar a CLI, você precisa configurar suas credenciais. A CLI busca essas informações em variáveis de ambiente ou em um arquivo `.env` na raiz do projeto.

### Variáveis Obrigatórias:
*   `ADAPTA_LOGIN`: Seu e-mail de acesso à plataforma Adapta.
*   `ADAPTA_PASSWORD`: Sua senha de acesso.

### Variáveis Opcionais:
*   `ADAPTA_MODEL`: Define o modelo padrão para os comandos (ex: `claude45h`, `gpt54`). Se não definido, a CLI poderá solicitar a escolha interativamente.
*   `ADAPTA_DATA_DIR`: Caminho para salvar dados locais (personas, cookies, estados). O padrão é `~/.adapta`.
*   `ADAPTA_PIPELINE_DB_PATH`: Caminho customizado para o banco de dados do pipeline.
*   `ADAPTA_SKILL_CREATE_DB_PATH`: Caminho customizado para o banco de dados de criação de skills.

**Dica:** Crie um arquivo `.env` na raiz do seu workspace para não precisar exportar as variáveis manualmente a cada sessão.

---

## 1. Configuração e Utilidade

### `import-cookies`
**Para que usar:** Para autenticar a CLI com a plataforma Adapta. A CLI utiliza os cookies da sua sessão web ativa para realizar chamadas à API sem precisar configurar chaves complexas manualmente.
**Como usar:** Exporte os cookies do seu navegador (após logar na plataforma Adapta) e salve em um arquivo de texto. Em seguida, importe-os para a CLI.
**Exemplo:**
```bash
adapta import-cookies --input cookies.txt
```

### `models`
**Para que usar:** Para descobrir quais modelos de IA estão disponíveis no seu plano da Adapta, visualizar suas chaves de acesso (`key`) e ler um resumo de suas capacidades (ex: qual o melhor modelo para código, raciocínio avançado ou tarefas rápidas).
**Como usar:** Rode o comando sem argumentos para imprimir a tabela de modelos.
**Exemplo:**
```bash
adapta models
```

---

## 2. Interação Direta

### `prompt`
**Para que usar:** Executar solicitações de tiro único (zero-shot) para um modelo específico. É o "canivete suíço" da CLI, ideal para revisões de código isoladas, tirar dúvidas arquiteturais rápidas, tradução, ou solicitar a criação de um artefato único.
**Como usar:** Você pode passar o prompt como texto puro ou via um arquivo markdown. Suporta também o envio de arquivos locais anexados, uso de personas e streaming no terminal. O resultado pode ser impresso no terminal ou salvo diretamente em um arquivo.
**Exemplos:**
```bash
# Prompt rápido lendo a saída no próprio terminal
adapta prompt --model claude45h --prompt "Explique o padrão de design Adapter em Python"

# Lendo prompt de um arquivo, anexando código e salvando o output
adapta prompt --model gpt54 --prompt-file instrucoes.md --file src/main.py --output analise.md
```

### `chat`
**Para que usar:** Iniciar uma conversa contínua e interativa diretamente no seu terminal, preservando o histórico e o contexto a cada mensagem enviada. Útil para sessões de depuração conjunta (rubber duck debugging) ou exploração interativa de ideias.
**Como usar:** Selecione um modelo e inicie o chat. Você pode opcionalmente anexar um arquivo no momento da inicialização.
**Exemplo:**
```bash
adapta chat --model deepseekreasoner --file erro_em_producao.log
```

---

## 3. Fluxos Complexos e Decisão

### `persona`
**Para que usar:** Capturar, gerenciar e armazenar perfis comportamentais e de conhecimento ("personas"). Personas garantem que a IA adote um ponto de vista específico e aprofundado (ex: "Especialista em Segurança", "Desenvolvedor Frontend Sênior", "CFO"). Esses perfis são altamente recomendados para guiar respostas no comando `prompt` e são a base estrutural do comando `debate`.
**Como usar:** A CLI oferece um formulário interativo no terminal. Ela salvará um `.json` com as respostas e um `.md` otimizado para o prompt.
**Exemplos:**
```bash
# Modo de entrevista interativa no terminal
adapta persona --model claude45h

# Listar personas existentes
adapta persona --list
```

### `debate`
**Para que usar:** Simular uma "mesa redonda" ou "comitê de decisão" entre múltiplos agentes de IA (cada um encenando uma persona diferente). Excelente para decisões de engenharia de alto risco, avaliações arquiteturais, e para evitar pontos cegos e viés de confirmação antes de iniciar um desenvolvimento complexo.
**Como usar:** Você deve fornecer um arquivo `.json` de configuração (`--config`) mapeando as personas aos agentes, definir a quantidade de rodadas (`--rounds`) que eles irão argumentar, e o arquivo contendo o problema a ser debatido (`--prompt-file`).
**Exemplo:**
```bash
adapta debate --config debate-agentes.json --rounds 3 --prompt-file problema-arquitetura.md --output consenso_final.md
```

---

## 4. Processamento em Lote e Pipelines

### `destilador`
**Para que usar:** Processar grandes volumes de texto ou documentos gigantes, "destilando" e resumindo a informação apenas para o essencial. Perfeito para encurtar manuais, atas de reunião imensas ou extrair a inteligência principal de dezenas de PDFs.
**Como usar:** Especifique um arquivo individual ou um diretório inteiro de entrada, e o destino para salvar o material sumarizado.
**Exemplo:**
```bash
adapta destilador --input-dir raw_pdfs/ --output-dir conhecimento_destilado/ --log
```

### `pipeline`
**Para que usar:** Automatizar o processamento de dados utilizando o motor assíncrono da Adapta. Útil para submeter dezenas de arquivos à plataforma de uma vez, seja para montar bases de conhecimento estruturadas ou indexações de Retrieval-Augmented Generation (RAG).
**Como usar:** Passe a pasta de documentos, a pasta de destino e (opcionalmente) configure bancos de dados auxiliares locais.
**Exemplo:**
```bash
adapta pipeline --input-dir arquivos_brutos/ --output-dir saida_pipeline/ --mode upload
```

### `skill-create`
**Para que usar:** Ler um conjunto de diretrizes, manuais ou documentações (via um pipeline) e extrair inteligentemente metadados e instruções rigorosas para gerar "Skills" automatizadas prontas para a nuvem.
**Como usar:** Aponta-se um diretório de arquivos crus e a CLI abstrai e consolida esse conhecimento na forma de arquivos padronizados de habilidades (skills).
**Exemplo:**
```bash
adapta skill-create --input-dir manuais_tecnicos/ --output-dir novas_skills/
```

---

## 5. Gerenciamento Remoto na Plataforma Web

A Adapta permite salvar histórico e customizações na nuvem associada à sua conta. A CLI reflete essas funções nos comandos abaixo.

### `folder`
**Para que usar:** Organizar sua área de trabalho e histórico de chats na plataforma web da Adapta. Ao organizar pastas via CLI, você pode posteriormente direcionar comandos de `prompt` para criar chats organizados remotamente (usando `--folder` no `adapta prompt`).
**Como usar:** Utilize as flags booleanas para escolher a ação.
**Exemplos:**
```bash
adapta folder --list
adapta folder --create --name "Projetos de Migração"
adapta folder --delete --name "Projetos de Migração"
```

### `list-files`
**Para que usar:** Listar quais arquivos (e seus respectivos IDs e caminhos de armazenamento) você já enviou/fez upload previamente para a nuvem da Adapta, permitindo o reuso.
**Como usar:**
```bash
adapta list-files
```

### `skill`
**Para que usar:** Gerenciar as Skills (instruções de sistema predefinidas) armazenadas na **sua conta na nuvem da Adapta**. Diferente das skills da própria CLI (que vivem localmente em `.agents/skills`), esse comando cria, lista e ativa habilidades que a sua instância web da Adapta usará nativamente.
**Como usar:** O comando concentra o CRUD (Create, Read, Update, Delete) através de flags.
**Exemplos:**
```bash
# Listar todas as suas skills da nuvem
adapta skill --list

# Criar uma skill diretamente na plataforma
adapta skill --create --title "Revisor Sênior" --description "Revisa código focado em performance" --instruction "Sempre analise complexidade de tempo..."

# Ativar uma skill
adapta skill --enable --id "id-da-skill"
```
