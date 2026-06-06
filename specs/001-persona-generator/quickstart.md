# Quickstart: Persona Generator

## Objective

Implementar a feature de geração de persona preservando o fluxo doc-first, TDD e validação operacional do projeto.

## Delivery Order

1. Atualizar a documentação impactada em `docs/` antes de testes e implementação.
2. Criar testes unitários para o novo serviço e para o fluxo interativo do comando.
3. Executar os testes para garantir estado vermelho inicial.
4. Implementar o comando `persona` e o serviço associado com a menor mudança correta.
5. Adicionar testes de integração do comando cobrindo geração mínima, sobrescrita e cleanup.
6. Executar a suíte relevante e corrigir regressões.

## Suggested Implementation Scope

1. Adicionar um comando `persona` em `src/adapta/cli.py`.
2. Adicionar `src/adapta/services/persona_service.py` com:
   - construção do questionário em formato estruturado
   - validação/normalização do nome
   - montagem do prompt final com JSON preservando vazios
   - resolução multiplataforma do caminho lógico `~/.adapta/persona/{nome-persona}.md`
   - orquestração de geração e persistência
3. Reutilizar `registry` para resolver `claude`.
4. Reutilizar o padrão de cleanup efêmero já existente no cliente/serviços.

## Validation Focus

1. Nome inválido deve ser recusado logo na primeira pergunta.
2. Cargo vazio deve impedir conclusão do questionário.
3. Campos opcionais vazios devem seguir como strings vazias no payload.
4. Arquivo existente deve pedir confirmação antes da gravação.
5. Falha de cleanup remoto não deve apagar ou invalidar arquivo local já salvo.
6. O usuário deve receber mensagem clara com o caminho final quando houver sucesso.
7. A resolução do diretório home deve funcionar corretamente em Linux e Windows.

## Suggested Test Commands

```text
pytest tests/unit/test_cli.py tests/unit/test_persona_service.py
pytest tests/integration/test_persona_command.py tests/integration/test_chat_cleanup.py
pytest
```

## Documentation Checklist

- Atualizar `docs/features.md`
- Atualizar `docs/code-map.md`
- Atualizar `docs/arquitetura.md`
- Atualizar `docs/modelo-dados.md`
- Atualizar `docs/integracoes.md`
- Atualizar `docs/licoes-aprendidas.md` se houver incidente relevante durante a implementação
