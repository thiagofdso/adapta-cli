# Quickstart: Destilador no CLI

## Pré-requisitos

- Variáveis `ADAPTA_LOGIN` e `ADAPTA_PASSWORD` configuradas.
- Um arquivo de entrada compatível com o pipeline de destilação.
- Ambiente local capaz de executar `python -m adapta.cli` ou `adapta`.

## Executar o comando

```bash
python -m adapta.cli destilador --input ./livro.pdf --output ./livro-destilado.md
```

## Executar em lote por diretório

```bash
python -m adapta.cli destilador --input-dir ./livros --output-dir ./docs_livros
```

## Fluxo esperado

1. validar a origem de entrada, por arquivo ou por diretório
2. consultar a listagem remota e reaproveitar uploads existentes quando o mesmo nome já estiver disponível
3. validar o destino de saída correspondente
4. iniciar o processamento interno do pipeline de destilação
5. gerar as dimensões intermediárias necessárias
6. consolidar o resultado em `--output` ou em arquivos correspondentes dentro de `--output-dir`
7. limpar artefatos temporários e remotos em modo best-effort

## Inspecionar arquivos remotos existentes

```bash
python -m adapta.cli list-files
```

## Exemplos relacionados de anexos no CLI

```bash
python -m adapta.cli prompt --model gpt --prompt "resuma os anexos" --file ./a.pdf,./b.pdf
python -m adapta.cli debate --config ./debate.json --prompt "Discuta o documento" --rounds 2 --file ./a.pdf,./b.pdf
```

## Cenários de validação

- entrada inexistente em `--input` deve falhar antes do processamento
- diretório inexistente em `--input-dir` deve falhar antes do processamento
- saída não gravável em `--output` deve falhar com mensagem curta
- `--output-dir` inválido deve falhar com mensagem curta
- execução bem-sucedida deve criar ou sobrescrever o arquivo final solicitado, ou um arquivo por item no diretório de saída
- falhas durante o pipeline devem preservar artefatos úteis para análise quando aplicável
- o comando deve funcionar sem dependência de código externo ao repositório `adapta-cli`
- o mesmo arquivo remoto não deve ser reenviado quando já existir com o mesmo nome na conta
