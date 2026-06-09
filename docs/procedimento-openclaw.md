# Procedimento operacional com Adapta CLI no OpenClaw

## Objetivo

Documentar o procedimento prático que estamos usando com o `adapta` dentro do OpenClaw para executar pesquisas técnicas em lote, salvar resultados por prompt e acompanhar módulos de curso com previsibilidade.

---

## Cenário de uso atual

Estamos usando o Adapta CLI como motor de execução de pesquisas técnicas para produção de conteúdo de curso, especialmente quando há:

- múltiplos prompts por módulo
- necessidade de salvar cada resposta em arquivo próprio
- revisão posterior humana
- reaproveitamento de contexto por arquivo/prompt
- necessidade de separar geração, revisão e fechamento do módulo

Exemplo real de uso:
- módulo 08 concluído dessa forma
- módulo 09 disparado no mesmo padrão

---

## Estratégia operacional adotada

### 1. Organização por módulo

Cada módulo segue esta estrutura:

```text
cursos/openclaw-ai-employees/modulo-XX/
├── prompts/
└── resultados/
```

Regras práticas:
- cada prompt `.md` representa um item numerado do módulo
- cada resultado salvo em `resultados/` mantém o nome correspondente do prompt
- o fechamento do módulo só acontece após revisão humana ou validação explícita

### 2. Fluxo que estamos usando

```text
1. Preparar prompts numerados do módulo
2. Executar geração em lote
3. Salvar um arquivo por prompt em resultados/
4. Monitorar execução e identificar falhas parciais
5. Regenerar manualmente apenas itens problemáticos
6. Revisar resultados
7. Fechar o módulo
8. Registrar progresso em BrainRepo
```

### 3. Papel do OpenClaw nesse fluxo

O OpenClaw está sendo usado para:
- localizar prompts e resultados
- acionar execuções do módulo
- monitorar andamento
- sobrescrever arquivos com versões regeneradas
- consolidar status final do módulo
- registrar o projeto e progresso no BrainRepo

---

## Como o Adapta CLI entra no processo

Pelo código e documentação atual, o `adapta` suporta os seguintes comandos relevantes:

- `adapta prompt`
- `adapta chat`
- `adapta models`
- `adapta list-files`
- `adapta import-cookies`
- `adapta logout`
- `adapta persona`
- `adapta debate`
- `adapta destilador`
- `adapta pipeline`
- `adapta folder`
- `adapta skill`
- `adapta context`
- `adapta expert`

Essas opções estão implementadas em `src/adapta/cli.py`.

---

## Procedimento recomendado para módulos de curso

### Modo principal: prompt por arquivo + saída em arquivo

Para conteúdo de curso, o modo mais previsível é:

```bash
adapta prompt --model <modelo> --prompt-file <prompt.md> --output <resultado.md>
```

Exemplo:

```bash
adapta prompt \
  --model sonar \
  --prompt-file cursos/openclaw-ai-employees/modulo-09/prompts/01-custos-em-plataformas-agentic.md \
  --output cursos/openclaw-ai-employees/modulo-09/resultados/01-custos-em-plataformas-agentic.md
```

### Por que esse modo é o preferido

Porque ele:
- reduz erro manual de copiar e colar
- preserva rastreabilidade entre prompt e resultado
- permite reexecução isolada de itens com falha
- facilita revisão humana depois
- encaixa bem no fluxo por módulo

---

## Quando usar cada comando do Adapta

### `adapta prompt`

Use para:
- gerar resposta técnica a partir de um prompt fechado
- salvar pesquisa por item do curso
- comparar modelos trocando `--model`
- anexar arquivos com `--file`
- aplicar persona com `--persona`

Formato comum:

```bash
adapta prompt --model <modelo> --prompt-file <arquivo> --output <saida>
```

### `adapta persona`

Use para:
- criar personas reutilizáveis
- manter perfis de análise
- regenerar persona por JSON
- atualizar persona existente

Útil quando o mesmo perfil de análise será aplicado em vários prompts.

### `adapta debate`

Use para:
- decisões com múltiplas perspectivas
- análise contraditória
- avaliação com agentes/personas diferentes
- síntese mais robusta para temas difíceis

No nosso fluxo atual de curso, debate é mais adequado para:
- planejamento de produto
- revisão crítica
- refinamento de proposta
- análise comparativa complexa

Não é o modo principal para geração em lote de um módulo inteiro.

### `adapta pipeline`

Use para:
- processamento em diretório
- fluxos maiores com estado persistido
- operações de lote com SQLite local

Esse comando é mais apropriado quando o problema é pipeline documental/operacional, não apenas geração de um arquivo final por prompt.

### `adapta destilador`

Use para:
- destilar PDFs ou textos longos
- gerar consolidados por documento
- processar diretórios de documentos

Bom para transformar material bruto em insumo de aula, antes da fase de escrita final.

### `adapta models`

Use para:
- descobrir modelos disponíveis
- escolher modelo conforme velocidade, custo ou qualidade

### `adapta chat`

Use para:
- exploração interativa
- investigação manual
- iteração aberta antes de congelar um prompt final

Não é o modo ideal para geração numerada de módulos, porque perde previsibilidade frente ao `prompt --prompt-file --output`.

---

## Modelos disponíveis hoje

Segundo a skill e o registro atual, os modelos expostos incluem:

- `one`
- `onepro`
- `onesuperfast`
- `gpt54`
- `gpt51`
- `gemini31`
- `geminiflash`
- `claude46`
- `claude45h`
- `deepseekreasoner`
- `deepseek`
- `grok`
- `kimi`
- `minimax`
- `glm5`
- `llama4`
- `sonar`
- `qwen35`

Observação prática:
- para pesquisa com foco em web, `sonar` é especialmente útil
- para contexto extenso e raciocínio pesado, modelos topo de linha podem fazer mais sentido
- para tarefas repetitivas ou mais baratas, usar um modelo mais econômico costuma ser melhor

---

## Regras operacionais que estamos adotando

### 1. Um prompt = um arquivo
Não misturar múltiplos tópicos em um mesmo arquivo quando o objetivo é fechar um módulo com rastreabilidade.

### 2. Um resultado = um arquivo final
Cada item deve gerar um markdown próprio em `resultados/`.

### 3. Reexecução seletiva
Se houver falha parcial, regenerar só os itens afetados.

### 4. Revisão humana antes do fechamento
Resultado salvo não significa módulo concluído.

### 5. Fechamento explícito do módulo
O módulo só fecha quando os itens pendentes foram corrigidos e revisados.

### 6. Atualização do BrainRepo
Ao concluir ou avançar de forma relevante em um módulo, registrar o progresso no BrainRepo.

---

## Limitações observadas no uso real

Durante execuções longas em lote, podem ocorrer:
- erros intermediários mesmo com fechamento operacional posterior
- respostas parciais
- necessidade de regeneração manual de itens específicos
- limites operacionais/diários no chat

Por isso, o procedimento atual inclui:
- monitoramento do lote
- marcação dos arquivos com ressalva
- regeneração manual do que falhou
- validação humana final

---

## Heurística prática: quando usar o quê

### Use `adapta prompt` quando:
- já existe um prompt bem definido
- você quer um arquivo final por item
- o trabalho precisa ser reproduzível
- haverá revisão posterior

### Use `adapta chat` quando:
- você ainda está explorando o problema
- precisa iterar rapidamente
- o prompt ainda não está maduro

### Use `adapta debate` quando:
- a decisão pede múltiplas perspectivas
- você quer contraditório estruturado
- o tema é ambíguo, estratégico ou controverso

### Use `adapta destilador` quando:
- a entrada é um documento bruto longo
- você quer extrair síntese ou estrutura

### Use `adapta pipeline` quando:
- o problema é um fluxo documental maior
- você precisa persistência operacional
- há múltiplas etapas em lote

---

## Referências internas

- `README.md`
- `docs/features.md`
- `docs/code-map.md`
- `docs/integracoes.md`
- `src/adapta/cli.py`
- `debate-kits/README.md`

---

## Resumo curto

O procedimento que estamos usando com Adapta + OpenClaw é:

- organizar prompts por módulo
- executar geração por arquivo
- salvar resultados individualmente
- monitorar falhas parciais
- regenerar só o necessário
- revisar manualmente
- fechar o módulo explicitamente
- registrar progresso no BrainRepo

Hoje, para módulos de curso, o comando principal é:

```bash
adapta prompt --model <modelo> --prompt-file <prompt.md> --output <resultado.md>
```
