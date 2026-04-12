# Upload-First Document AI Debugging

**Extracted:** 2026-04-12  
**Context:** Fluxos CLI que enviam arquivos para um backend de IA com SSE e depois falham com resposta vazia ou comportamento diferente da interface web.

## Problem
O upload do arquivo funciona, mas a resposta final do modelo vem vazia, truncada ou diferente do comportamento observado na interface web.

## Solution
Validar o pipeline em camadas, sem presumir que o problema está no upload:
1. Confirmar no HAR se o upload retorna `200` e metadados válidos.
2. Comparar o payload do endpoint de stream da interface com o payload do cliente local.
3. Alinhar campos estruturais críticos:
   - `chatId` em formato UUID-like puro
   - `messageId`
   - `messages[].id`
   - `parts` com arquivo antes do texto
   - `referer` compatível com a interface
4. Testar o stream bruto SSE diretamente antes de culpar timeout ou parser.
5. Se o stream bruto tiver `text-delta`, o problema está no agregador/extrator local, não no backend.

## Example
Sinais úteis:
- HAR mostra `POST /api/file/upload` com `200 OK`
- HAR mostra `POST /api/chat/stream/v1` retornando `text/event-stream`
- inspeção bruta do SSE revela eventos `text-delta` com conteúdo real
- chamada de alto nível ainda retorna `ChatCompletionResult(... text: '')`

Conclusão:
- upload ok
- backend ok
- bug no payload final ou no agregador local

## When to Use
- Quando um comando CLI com upload de PDF/documento funciona na interface web mas falha localmente
- Quando há suspeita de timeout, mas o HAR mostra stream ativo
- Quando a resposta final vem vazia apesar de o stream bruto conter texto
