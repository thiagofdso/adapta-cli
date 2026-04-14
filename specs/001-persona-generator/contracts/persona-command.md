# Contract: `persona` CLI Command

## Purpose

Expor um comando interativo que coleta respostas de persona, gera um markdown com modelo Claude e salva o resultado em uma pasta de personas sob o diretório home do usuário, compatível com Linux e Windows.

## Invocation

```text
adapta persona
```

## Interaction Contract

1. O comando inicia a entrevista em 6 blocos, mantendo a ordem definida na especificação.
2. A primeira pergunta solicita o nome da persona.
3. O nome é validado imediatamente.
4. Se o nome for inválido, o usuário recebe mensagem curta e o comando repete a pergunta até receber um nome válido ou ser interrompido.
5. A segunda pergunta solicita o cargo/título profissional.
6. O cargo é obrigatório.
7. As demais perguntas aceitam resposta vazia com Enter.
8. Ao final da coleta, o comando monta o JSON com todos os campos, preservando strings vazias.
9. O comando resolve o arquivo de destino na pasta de personas sob o diretório home real do usuário, equivalente ao local lógico `~/.adapta/persona/{nome-persona}.md`.
10. Se o arquivo já existir, o comando pede confirmação explícita antes de sobrescrever.
11. Se o usuário recusar, a execução termina sem alterar o arquivo existente.
12. Se a geração for bem-sucedida, o comando informa o caminho salvo.
13. Ao finalizar, o comando tenta excluir a conversa remota usada no processo.

## Output Contract

### Success

- O conteúdo final é salvo como markdown na pasta de personas sob o diretório home real do usuário.
- A saída ao usuário informa o caminho absoluto ou expandido do arquivo salvo.
- Se houver falha de cleanup remoto após o salvamento, a saída inclui um aviso sem marcar a geração como fracassada.

### User-controlled cancellation

- Se o usuário recusar a sobrescrita, o comando termina sem gravar novo conteúdo no destino existente.

### Error handling

- Erros de validação e falhas operacionais esperadas são mostrados em mensagem curta e acionável.
- O comando não deve exibir traceback verboso em erros esperados.
- O comando não deve deixar arquivo final vazio sendo apresentado como sucesso.

## Data Contract Sent To Generator

O payload textual enviado ao gerador deve conter o prompt-base fixo da feature e um JSON com estas chaves:

```json
{
  "nome": "",
  "cargo": "",
  "setor": "",
  "idade": "",
  "tamanho_empresa": "",
  "valores": "",
  "comunicacao": "",
  "senioridade": "",
  "objetivo_6_12m": "",
  "aspiracao_3_5a": "",
  "dia_perfeito": "",
  "dores": "",
  "tira_sono": "",
  "medos": "",
  "forma_trabalho": "",
  "inovacao": "",
  "aprendizado": "",
  "tom_voz": "",
  "maneirismos": "",
  "motiva_desmotiva": ""
}
```

## Test Contract

- Teste unitário do comando deve cobrir re-prompt para nome inválido.
- Teste unitário do serviço deve cobrir normalização do nome, montagem do payload e bloqueio de gravação quando a sobrescrita for recusada.
- Teste de integração deve cobrir o fluxo mínimo com `nome` e `cargo` apenas.
- Teste de integração deve cobrir confirmação de sobrescrita.
- Teste de integração deve cobrir tentativa de cleanup da conversa remota ao final.
