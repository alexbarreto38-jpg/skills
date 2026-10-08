# 0007 — Jobs no banco, Dramatiq + Redis, progresso por SSE

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

Análise e geração levam de segundos a muitos minutos, passam por várias etapas, podem
falhar no meio, precisam mostrar progresso em tempo real, ser canceladas e não podem rodar
duas vezes por um clique duplo ou uma reentrega da fila.

## Decisão

- O **estado do job vive no Postgres** (`jobs`, `job_events`), não na fila. A fila
  (Dramatiq sobre Redis) só transporta "rode o job X".
- `create_job` é idempotente por `(projeto, tipo, idempotency_key)` (índice único).
- O worker faz **claim atômico** (`UPDATE … WHERE status = 'QUEUED'`); se outra entrega já
  pegou o job, a mensagem é descartada.
- Cada etapa grava um `JobEvent` e é um checkpoint de cancelamento cooperativo.
- O frontend acompanha por **SSE** (`GET /jobs/{id}/events`, retomável com
  `Last-Event-ID`) ou por polling do histórico.
- Três backends de fila com a mesma interface: `dramatiq` (produção), `thread` (dev sem
  Redis), `inline` (testes, determinístico).

## Alternativas consideradas

- **Celery** — mais pesado de configurar e operar para o que usamos; Dramatiq tem
  semântica de retry e ack mais simples.
- **Estado na fila / resultado no backend da fila** — o histórico e o progresso
  sumiriam com a mensagem, e a UI não teria de onde ler eventos passados.
- **WebSocket** — bidirecional sem necessidade; SSE passa por proxies HTTP comuns e é
  trivial de retomar.

## Consequências

- A UI sobrevive a recarregar a página: o job e seus eventos estão no banco.
- Reentregas e cliques duplos são inofensivos.
- Cancelar não interrompe uma chamada de provider em andamento — o job para no próximo
  checkpoint.
- O banco recebe uma escrita por evento; com volume alto, compactar ou expirar eventos
  antigos será necessário.
