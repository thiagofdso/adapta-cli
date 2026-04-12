# Research: Build Adapta CLI

## Decision 1: Usar projeto Python com `pyproject.toml` e layout `src/`

- Decision: Estruturar a CLI como um projeto Python único com `pyproject.toml`, pacote em `src/adapta` e entry point de console.
- Rationale: O layout `src/` evita imports acidentais a partir da raiz, representa melhor o comportamento do pacote instalado e mantém a CLI empacotável desde o início.
- Alternatives considered: Estrutura flat na raiz foi descartada por aumentar o risco de diferenças entre execução local e pacote instalado.

## Decision 2: Usar Typer para a interface de linha de comando

- Decision: Implementar a CLI com Typer e subcomandos explícitos `prompt` e `chat`.
- Rationale: Typer reduz boilerplate, facilita ajuda automática, entradas interativas, opções tipadas e testes de CLI, mantendo a implementação pequena.
- Alternatives considered: `argparse` foi descartado por ser mais verboso para prompts e UX interativa; Click puro foi descartado por não trazer vantagem clara frente ao Typer neste escopo.

## Decision 3: Carregar configuração com `.env` local e campos tipados

- Decision: Criar um módulo de configuração próprio para a CLI, baseado em `.env`, com suporte a `ADAPTA_LOGIN`, `ADAPTA_PASSWORD` e `ADAPTA_MODEL`.
- Rationale: O projeto Adapta atual usa `pydantic-settings` e `dotenv`, com variáveis `ADAPTA_LOGIN` e `ADAPTA_PASSWORD` como base de autenticação. A CLI deve manter a mesma convenção, mas apontando para o `.env` da própria raiz do projeto `adapta-cli`.
- Alternatives considered: Reusar `src/config.py` diretamente foi descartado porque ele acopla o caminho do `.env` ao repositório original e traz comportamento de reload que não é necessário para uma CLI de processo curto.

## Decision 4: Reaproveitar o comportamento mínimo do cliente e não a nomenclatura `generator`

- Decision: Reaproveitar os padrões de `AdaptaClientV2`, `BaseContentGenerator` e `app_chat.py`, mas expor uma estrutura reformulada com registro de modelos e serviços.
- Rationale: No Adapta atual, cada modelo é essencialmente uma configuração de `model_name` sobre um cliente compartilhado. A nova CLI pode reduzir isso a um registro de modelos e um adaptador enxuto, sem carregar a terminologia de `generator` para dentro da nova base.
- Alternatives considered: Copiar integralmente `generators_v2` foi descartado por introduzir classes demais para uma CLI pequena e por dificultar a leitura do fluxo principal.

## Decision 5: Manter comandos síncronos com fronteira assíncrona interna

- Decision: Deixar os comandos da CLI síncronos e encapsular o uso do cliente assíncrono em chamadas com `asyncio.run()`.
- Rationale: O cliente do Adapta é assíncrono e depende do loop corrente; uma única fronteira assíncrona por comando evita hacks de loop como os usados no Streamlit e simplifica cleanup com `try/finally`.
- Alternatives considered: Reutilizar o padrão de loop compartilhado do `app_chat.py` foi descartado por ser específico de UI interativa com Streamlit.

## Decision 6: Adotar TDD estrito em duas etapas

- Decision: Seguir uma abordagem doc-first antes do TDD: primeiro atualizar a documentação negocial e técnica, depois escrever testes unitários de configuração, registro de modelos, regras de CLI, leitura de prompt, escrita de saída e ciclo de vida do chat; só depois escrever a implementação mínima. Após a suíte unitária ficar verde, adicionar testes de integração.
- Rationale: O usuário quer documentação antes do desenvolvimento e dos testes. Essa ordem deixa explícito o contexto funcional e técnico antes de codar, e mantém os benefícios de TDD para validar comportamento local antes da integração real.
- Alternatives considered: Escrever testes antes de documentar foi descartado por conflitar com a diretriz doc-first; escrever integração desde o início foi descartado por misturar problemas de rede, credenciais e ergonomia de CLI antes de validar a lógica local.

## Decision 7: Testes de integração devem usar casos simples e deterministicamente verificáveis

- Decision: Os testes de integração vão executar a CLI real com `.env` disponível e usar prompts simples, como solicitar que o modelo responda apenas `2` para `1+1`.
- Rationale: Prompts curtos e restritivos reduzem variabilidade na resposta e permitem validação objetiva em stdout e arquivos de saída.
- Alternatives considered: Prompts abertos foram descartados por elevarem a chance de respostas longas ou não determinísticas.

## Decision 8: Encerrar e excluir chats remotos ao sair

- Decision: Toda sessão de chat criada pela CLI deve tentar excluir o chat remoto ao encerramento normal ou por erro controlado.
- Rationale: O `app_chat.py` já mostra o padrão de limpar o chat remoto em reset, e o requisito da feature exige que a sessão não permaneça na Adapta após o uso.
- Alternatives considered: Preservar chats para retomada posterior foi descartado por conflitar diretamente com o requisito do usuário.

## Decision 9: Expor logs apenas por opção explícita de execução

- Decision: Adicionar um parâmetro global `--log` para ativar logs quando necessário, mantendo a CLI sem logs operacionais por padrão.
- Rationale: O uso mais comum deve exibir apenas a resposta final, enquanto execuções de diagnóstico podem optar por `--log info` ou `--log debug` conforme a necessidade.
- Alternatives considered: Exigir `--no-log` foi descartado por adicionar ruído ao caso padrão; fixar um único nível de log ou depender apenas de variável de ambiente também foi descartado por reduzir controle por execução.

## Decision 10: Fornecer scripts de instalação separados para origem local e remota

- Decision: Incluir scripts de instalação na pasta `scripts/`, um para instalar a partir do diretório local do projeto e outro para instalar a partir de um repositório remoto informado pela pessoa usuária.
- Rationale: Isso reduz fricção para colocar `adapta` no sistema e torna explícitos os dois modos de distribuição pedidos, sem exigir que a pessoa conheça de antemão os comandos de empacotamento Python.
- Alternatives considered: Confiar apenas em documentação textual de instalação foi descartado por não atender ao pedido de ter um script executável para o processo.

## Decision 11: Incluir `Makefile` como atalho operacional e de testes

- Decision: Adicionar um `Makefile` com alvos mínimos para testes, prompt e chat, incluindo uso simples como `make prompt` e `make chat`.
- Rationale: O `Makefile` reduz a necessidade de lembrar comandos longos, melhora a ergonomia local e cria uma interface curta para fluxos recorrentes de desenvolvimento e validação.
- Alternatives considered: Depender apenas dos comandos diretos da CLI foi descartado por não atender ao requisito explícito de usar `make` como atalho principal.
