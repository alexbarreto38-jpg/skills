# Arquitetura

Este documento descreve como o VideoDNA Studio está organizado e o caminho de um vídeo
do upload ao resultado. As decisões e suas alternativas estão nos
[ADRs](architecture-decisions/).

## Visão geral

```
apps/web (Next.js) ──REST/SSE──▶ apps/api (FastAPI) ──▶ PostgreSQL
        │                              │  └─ jobs ──▶ Redis ──▶ workers (Dramatiq)
        └──PUT/GET assinados──▶ S3 / MinIO ◀──────────────────────┘
                                                        │
                                              AI Orchestrator ──▶ adapters
```

O backend é um **monólito modular**: um único pacote Python (`videodna`) instalado numa
única imagem, que roda como API (`uvicorn videodna.main:app`) ou como worker
(`videodna worker`). Os módulos têm dependências numa só direção:

```
api ──▶ services ──▶ domain            (domain não faz I/O nem importa nada acima)
            │  └───▶ orchestrator ──▶ adapters (mock, local, reais)
            ├──▶ media (FFmpeg)
            ├──▶ storage (local, S3)
            ├──▶ jobs (fila, eventos)
            └──▶ db (SQLAlchemy)
```

| Módulo | Responsabilidade |
|--------|------------------|
| `domain/` | Schema do Video DNA, vocabulário (verbos, predicados, classes), operações de edição e `apply_operations`, análise de impacto, locks. Puro e testável sem banco. |
| `services/` | Casos de uso: projetos, upload, análise (pipeline, montagem, persistência), edição, sugestões, previews, geração (planner, runner), versões, métricas, retenção. |
| `orchestrator/` | Capabilities, descriptors, registry, router, gateway (timeout/retry/fallback), interfaces dos 10 tipos de provider e os adapters. |
| `media/` | ffprobe, detecção de shots, keyframes, cores, proxy, cortes, splice, concat, mux, vídeo sintético. |
| `storage/` | Interface única; backend local (URLs assinadas pela API) e S3 (presign, multipart). |
| `jobs/` | `create_job` idempotente, claim atômico, eventos, cancelamento, filas `inline`/`thread`/`dramatiq`. |
| `api/` | App FastAPI, rotas, schemas camelCase, auth, rate limit, tratamento de erro uniforme. |
| `db/` | Modelos SQLAlchemy 2.0 (21 tabelas) e sessão. |

## Fluxo 1 — upload e análise

```
POST /projects/{id}/uploads ─▶ URLs assinadas por parte ─▶ navegador PUT direto no storage
POST .../complete ─▶ valida partes ─▶ create_job(ANALYSIS) ─▶ fila
worker:
  A  técnico     ffprobe: duração, fps, resolução, codecs, áudio      local
     ingestão    sha256, proxy 720p, poster                           local
  B  shots       scene score por frame + blackdetect, pico adaptativo local
  C  keyframes   início/meio/fim + intervalo, cores dominantes        local
     narrativa   VideoAnalyzerProvider (multimodal, sobre o proxy)    IA
     detecção    ImageAnalyzerProvider só nos keyframes (+ OCR)       IA
     tracking    TrackingProvider por shot                            IA
     áudio       SpeechProvider                                       IA
     montagem    consenso, confiança, IDs persistentes, revisão       local
  ─▶ VideoDNA validado ─▶ JSON imutável + linhas normalizadas
```

Pontos de projeto:

- **Local primeiro.** Tudo que é determinístico roda antes e é reaproveitado pelas etapas
  de IA, que recebem só o necessário (o proxy, alguns keyframes) — nunca todos os frames.
- **Detecção de shots adaptativa.** Um único passe do FFmpeg imprime o *scene score* de
  cada frame e os trechos pretos. Um corte é um pico local (≥ 3× a vizinhança, acima de um
  piso), o que acha cortes entre planos de luminância parecida que um limiar fixo perde.
- **Consenso.** O detector e o modelo multimodal são comparados; divergência em elemento
  essencial vira `needsReview` com alternativas ("Copo de vidro / Taça?"), mostradas na UI
  como "Não tenho certeza sobre este elemento".
- **Reuso.** Mesmo conteúdo (hash) + mesma versão de pipeline + mesmo modo + mesmos cortes
  ⇒ as camadas de IA são reaproveitadas sem custo.

## Fluxo 2 — edição

```
editor ─▶ GET /entities/{id}/suggestions        cards contextuais (cache por elemento)
       ─▶ POST /projects/{id}/impact            impacto sem salvar (card antes de aplicar)
       ─▶ POST /projects/{id}/edits             cria EditOperation(ACTIVE)
       ─▶ POST .../edits/undo | redo            muda o status das operações
DNA atual = apply_operations(DNA original, operações ACTIVE em ordem)
```

O DNA original nunca muda. Undo marca a última operação ativa como `UNDONE`; redo
reativa a mais antiga desfeita; uma nova edição descarta (`DISCARDED`) a pilha de redo.
Versões guardam o conjunto de operações e podem ser restauradas. Detalhes em
[video-dna.md](video-dna.md).

## Fluxo 3 — plano e geração

```
POST /projects/{id}/generation-plan
  impacto de cada operação ─▶ agrupado por shot ─▶ estratégia mais leve viável
  ─▶ roteador escolhe provider/modelo por passo ─▶ custo estimado + teto com reparos
  ─▶ plano congelado (operações + fingerprint)          [usuário revisa e confirma]
POST /projects/{id}/generate  (Idempotency-Key)
worker, por shot:
  PASSTHROUGH ─▶ corta do original (custo zero)
  demais      ─▶ provider ─▶ QA técnico (FFmpeg) + inspetor de IA
                 └─ issue ≥ severidade mínima ─▶ reparo localizado (janela) ─▶ splice
                    até o limite do modo (1/2/3) e dentro do orçamento
  ─▶ concat dos shots ─▶ mux do áudio original ─▶ saída + provenance ─▶ nova versão
```

**Estratégias**, da mais leve à mais pesada:
`PASSTHROUGH < ATTRIBUTE_EDIT < LOCALIZED_EDIT < BACKGROUND_REPLACEMENT <
SHOT_RECONSTRUCTION < FULL_REGENERATION`. Cada tipo de mudança tem um peso de
complexidade (cor 1, objeto 2, ambiente inteiro 4, troca de personagem 5…, +1 se houver
física/interação); quando a soma num shot passa do limiar do modo (ECONOMY 10, BALANCED 8,
MAX 6), uma reconstrução única do shot sai melhor que várias edições leves encadeadas —
artefatos se acumulam a cada passada. No ECONOMY, ambiente + edições locais abaixo do
limiar viram `BACKGROUND_REPLACEMENT` seguido de `LOCALIZED_EDIT`.

**Locks** viram requisitos para o roteador: LOCK CAMERA exige `camera_preservation`, LOCK
MOTION exige `motion_preservation`, edições localizadas exigem `mask_input`, personagens em
vários shots exigem `reference_images` (Character Reference Pack). LOCK AUDIO preserva o
áudio original; LOCK TIMING preserva a duração de cada shot (o QA técnico confere).

**Plano desatualizado.** O plano guarda um *fingerprint* (análise + operações + modo +
resolução + locks). Se o usuário editar depois de planejar, o plano aparece como
desatualizado e a geração é recusada até um novo plano.

**Orçamento.** O teto inclui um reparo parcial por shot com risco físico mais o pior shot ×
tentativas restantes. Durante a execução, reparos pagos param se o gasto real passar do
estimado + `COST_OVERRUN_TOLERANCE`; o resultado então sai com `needsAttention`.

## Jobs, progresso e cancelamento

- Tabela `jobs` com herança de tabela única por tipo (`INGEST`, `ANALYSIS`, `PREVIEW`,
  `GENERATION`) e estados `QUEUED → PREPARING → ANALYZING|GENERATING → QA → REPAIRING →
  ASSEMBLING → COMPLETED|FAILED|CANCELLED`.
- `create_job` é idempotente por `(projeto, tipo, idempotency_key)` (índice único).
- O worker faz `UPDATE ... WHERE status = 'QUEUED'` (claim atômico); entregas duplicadas
  da fila não reexecutam o job.
- `JobReporter.progress()` grava um `JobEvent` e verifica cancelamento: é o checkpoint
  cooperativo. O SSE (`/jobs/{id}/events`) lê esses eventos e aceita `Last-Event-ID` para
  retomar.

## AI Orchestrator

```
AIOrchestrator.run(task, call)
  └─ AIProviderRouter.route(task)  ─▶ candidatos disponíveis, pontuados e justificados
       └─ invoke(adapter, timeout, retries, backoff)
            ├─ sucesso ─▶ ProviderUsage + CostEntry(ACTUAL)
            └─ cota/indisponível/timeout ─▶ ProviderUsage(falha) ─▶ fallback (1×)
```

O código de negócio pede uma **capability** (`video.localized_edit`, `qa.video_inspection`…)
e nunca importa um adapter. O registro, o roteamento e o checklist para providers reais
estão em [providers.md](providers.md).

## Modelo de dados

| Tabela | Conteúdo |
|--------|----------|
| `users`, `projects` | dono, nome, status, locks, modo de qualidade, configurações |
| `source_videos` | chave no storage, hash, metadados técnicos, proxy, poster, direitos, retenção |
| `video_analyses` | DNA original (JSON/JSONB), versão de pipeline, modo mock, resumo |
| `scenes`, `shots` | estrutura temporal |
| `entities` | herança de tabela única: personagem, cabelo, roupa, acessório, objeto, móvel, ambiente, parte de ambiente, iluminação, texto, áudio |
| `entity_tracks`, `actions`, `relationships` | movimento, ações (verbo + participantes) e grafo de cena |
| `edit_operations` | operações com status (`ACTIVE`/`UNDONE`/`DISCARDED`) e sequência |
| `suggestions` | cards por elemento, com página e contexto |
| `generation_plans` | plano congelado, fingerprint, custo estimado |
| `jobs`, `job_events` | execução e progresso |
| `generation_outputs` | vídeos finais/preview, segmentos por shot, tentativas, provenance |
| `qa_reports`, `qa_issues` | checagens e problemas por shot, com janela de tempo |
| `project_versions` | conjunto de operações nomeado e restaurável |
| `provider_usage`, `cost_entries` | cada chamada a provider (latência, erro, custo) e o ledger estimado × real |

## Frontend

- Next.js App Router; páginas são client components finos sobre hooks de
  `lib/queries.ts` (TanStack Query) e o store do editor (`lib/editor-store.ts`, Zustand).
- O client tipado vem de `packages/api-client` (gerado do OpenAPI) — nenhum tipo de API é
  escrito à mão.
- Progresso por SSE lido com `fetch` + stream (permite enviar o header de auth), com
  fallback para polling.
- O upload envia as partes, uma a uma e com progresso por byte, direto ao storage; ao
  retomar, pergunta ao servidor quais partes já chegaram e pula essas.
