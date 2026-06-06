# Debate Kits

Kits prontos para o comando `adapta debate`, usando o campo opcional `persona` por nome curto.

## Como funciona

- Cada arquivo `.json` define os agentes do debate.
- O campo `persona` usa apenas o nome curto da persona.
- O programa resolve automaticamente esse nome para `~/.adapta/persona/<nome>.md`.
- O tema principal do debate continua sendo informado por `--prompt`.

## Pré-requisitos

- As personas já devem existir em `~/.adapta/persona/`.
- Exemplos esperados: `cliente-cetico.md`, `cfo-rigoroso.md`, `tradutor-tecnico-para-negocios.md`.

## Kits Disponíveis

### `painel-clientes.json`

Quando usar:
- validar proposta comercial
- antecipar objecoes de venda
- comparar reacoes de perfis de cliente

Perfis:
- cliente-economico
- cliente-premium
- cliente-cetico

Exemplo:

```bash
adapta debate --config debate-kits/painel-clientes.json --rounds 2 --prompt "Avalie esta oferta comercial e diga o que faria cada perfil comprar ou desistir."
```

### `marketing-headlines.json`

Quando usar:
- guerra de headlines
- iteracao de anuncios
- refinamento de copy com contraditorio interno

Perfis:
- copywriter-competitivo
- editor-critico-de-copy

Exemplo:

```bash
adapta debate --config debate-kits/marketing-headlines.json --rounds 3 --prompt "Crie e refine headlines para uma landing page de consultoria em IA para empresas."
```

### `shark-tank.json`

Quando usar:
- treinar pitch
- pressionar business case
- revisar risco, retorno e consistencia

Perfis:
- cfo-rigoroso
- juridico-preventivo
- critico-construtivo

Exemplo:

```bash
adapta debate --config debate-kits/shark-tank.json --rounds 2 --prompt "Avaliem esta ideia de produto como se eu estivesse apresentando para comite executivo."
```

### `negociacao-contrato.json`

Quando usar:
- roleplay de negociacao contratual
- treino de argumentos de concessao e contrapartida
- identificacao de pontos de impasse

Perfis:
- comprador-agressivo
- fornecedor-irredutivel
- juridico-preventivo

Exemplo:

```bash
adapta debate --config debate-kits/negociacao-contrato.json --rounds 3 --prompt "Negociem um contrato anual de software com SLA, multa e clausulas de reajuste."
```

### `traducao-tecnico-negocio.json`

Quando usar:
- explicar arquitetura para negocio
- traduzir funcionalidade tecnica para impacto executivo
- alinhar precisao tecnica com clareza comercial

Perfis:
- tradutor-tecnico-para-negocios
- critico-construtivo
- realista-de-execucao

Exemplo:

```bash
adapta debate --config debate-kits/traducao-tecnico-negocio.json --rounds 2 --prompt "Traduzam para linguagem executiva os beneficios e limites de uma arquitetura orientada a eventos."
```

### `oficina-criativa.json`

Quando usar:
- brainstorming estilo Disney
- ideacao com contraditorio produtivo
- transformar ideias em plano robusto

Perfis:
- sonhador-estrategico
- realista-de-execucao
- critico-construtivo

Exemplo:

```bash
adapta debate --config debate-kits/oficina-criativa.json --rounds 3 --prompt "Criem e lapidem uma nova oferta de produto digital para consultorias B2B."
```

### `comite-decisao.json`

Quando usar:
- simular comite executivo
- testar uma proposta sob angulos complementares
- preparar decisao com contraditorio

Perfis:
- cfo-rigoroso
- juridico-preventivo
- realista-de-execucao
- critico-construtivo

Exemplo:

```bash
adapta debate --config debate-kits/comite-decisao.json --rounds 2 --prompt "Avaliem esta proposta de investimento em automacao com foco em aprovacao, ajustes ou rejeicao."
```

### `revisao-critica-proposta.json`

Quando usar:
- revisar proposta comercial ou tecnica
- melhorar clareza executiva
- encontrar buracos de argumento antes de enviar

Perfis:
- cliente-premium
- critico-construtivo
- tradutor-tecnico-para-negocios

Exemplo:

```bash
adapta debate --config debate-kits/revisao-critica-proposta.json --rounds 2 --prompt "Revisem criticamente esta proposta e devolvam os ajustes que deixariam o documento mais convincente."
```

### `analise-problema-negocio.json`

Quando usar:
- analisar problema complexo
- separar sintomas, causas e impactos
- construir plano de resposta priorizado

Perfis:
- realista-de-execucao
- critico-construtivo
- cfo-rigoroso
- realista-de-execucao

Exemplo:

```bash
adapta debate --config debate-kits/analise-problema-negocio.json --rounds 2 --prompt "Analisem por que a conversao comercial caiu e proponham uma resposta priorizada por valor e esforco."
```

### `proposta-executiva.json`

Quando usar:
- elaborar proposta ou documento complexo
- sair de contexto bruto para mensagem executiva
- fortalecer uma versao final para decisor

Perfis:
- realista-de-execucao
- tradutor-tecnico-para-negocios
- critico-construtivo
- cliente-premium

Exemplo:

```bash
adapta debate --config debate-kits/proposta-executiva.json --rounds 2 --prompt "Construam uma proposta executiva para um projeto de IA aplicada ao atendimento B2B."
```

## Observações

- Se quiser customizar um kit, duplique o JSON e ajuste `model`, `prompt` ou `persona`.
- Se quiser usar um arquivo de persona fora da pasta padrão, também é possível informar um caminho relativo ou absoluto no campo `persona`.
