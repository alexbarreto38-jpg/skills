# VideoDNA Studio

Plataforma para **remodelar vídeos com IA preservando a estrutura original**. O usuário
envia um vídeo de referência (sobre o qual tem direitos), o sistema o transforma num
**Video DNA** estruturado — shots, personagens, roupas, objetos, cenário, ações, relações,
narrativa, áudio — e o usuário edita esse DNA visualmente: "camiseta azul", "cabelo
cacheado", "copo → prato", "sala → apartamento moderno". Antes de gastar qualquer crédito,
o sistema calcula o **impacto** de cada alteração, monta um **Generation Plan** com custo
estimado por shot, gera shot a shot, roda **QA**, corrige localmente o que falhou e monta o
vídeo final mantendo áudio, duração e cortes.

> **Estado atual:** as três primeiras vertical slices funcionam de ponta a ponta em
> `AI_MOCK_MODE` — upload → análise → DNA → editor → sugestões → impacto → plano →
> geração → QA/reparo → montagem → comparação. Nenhum provider de IA real está ligado
> ainda, **de propósito**: cada um entra como um adapter, depois de conferida a
> documentação oficial dele (ver [docs/providers.md](docs/providers.md)).

---

## Sumário

- [Início rápido](#início-rápido)
- [O que funciona hoje](#o-que-funciona-hoje)
- [Arquitetura](#arquitetura)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Setup local (sem Docker)](#setup-local-sem-docker)
- [Docker](#docker)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Mock mode](#mock-mode)
- [Workers e jobs](#workers-e-jobs)
- [Banco de dados](#banco-de-dados)
- [Storage](#storage)
- [Providers de IA](#providers-de-ia)
- [API](#api)
- [Frontend](#frontend)
- [Testes](#testes)
- [Segurança, privacidade e uso responsável](#segurança-privacidade-e-uso-responsável)
- [Limitações conhecidas e roadmap](#limitações-conhecidas-e-roadmap)
- [Documentação adicional](#documentação-adicional)

---

## Início rápido

Só é preciso o [Docker Desktop](https://www.docker.com/products/docker-desktop/) aberto
(no Windows ele usa o WSL2, que o próprio instalador configura). O código está na branch
`claude/amazing-keller-uj680z` do repositório `alexbarreto38-jpg/skills`, na pasta
`videodna-studio`.

### Windows (PowerShell)

```powershell
cd $HOME
git clone --branch claude/amazing-keller-uj680z --depth 1 https://github.com/alexbarreto38-jpg/skills.git videodna
cd videodna\videodna-studio
powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
```

Sem Git: baixe o ZIP da branch
(`https://github.com/alexbarreto38-jpg/skills/archive/refs/heads/claude/amazing-keller-uj680z.zip`),
extraia, abra o PowerShell na pasta `videodna-studio` e rode a última linha acima.

O `iniciar.ps1` faz tudo sozinho e pode ser rodado de novo sem medo:

1. confere o Docker Desktop (e o abre, se estiver fechado);
2. baixa as imagens base **uma de cada vez, com novas tentativas** — redes instáveis
   não derrubam a instalação;
3. constrói as imagens do projeto (e as reconstrói sozinho depois de um `git pull`);
4. sobe tudo, espera ficar pronto e abre http://localhost:3000.

A primeira vez leva alguns minutos; as seguintes, segundos. Para parar:
`powershell -ExecutionPolicy Bypass -File .\parar.ps1` (projetos e vídeos continuam
guardados). Para atualizar: `git pull` e `.\iniciar.ps1` de novo.

### Linux e macOS

```sh
cd videodna-studio
docker compose up -d --build
```

### Endereços

| Serviço        | URL                          | Observação                                  |
|----------------|------------------------------|---------------------------------------------|
| Studio (web)   | http://localhost:3000        | entra direto como usuário dev (autologin)   |
| API + OpenAPI  | http://localhost:8000/docs   | Swagger gerado pelo FastAPI                 |

O stack padrão guarda os vídeos em disco (um volume compartilhado entre API e worker) e
não compila nada do código-fonte. O caminho S3 — upload direto do navegador para o bucket,
igual ao de produção — sobe com o MinIO pelo arquivo adicional `docker-compose.s3.yml`
(no Windows, `.\iniciar.ps1 -S3`); ver [Docker](#docker).

Depois, no navegador: **Novo projeto → envie um vídeo → confirme os direitos → Enviar e
analisar**. Sem um vídeo à mão, gere o vídeo sintético dos testes (12 s, 6 shots):

```sh
docker compose exec api videodna sample-video /tmp/sample.mp4
docker compose cp api:/tmp/sample.mp4 ./sample.mp4
```

Com [uv](https://docs.astral.sh/uv/) instalado, o projeto de demonstração inteiro — o caso
de teste §79 da especificação (menino, copo, mãe) com as cinco alterações — sai de um
comando, contra qualquer API no ar (Docker ou local):

```sh
cd apps/api
uv run videodna seed-demo --generate     # cria, envia, analisa, edita, planeja e gera
```

O `seed-demo` usa a mesma API pública que o frontend (upload multipart com URLs
assinadas inclusive) e imprime o plano com as dependências que o sistema reconheceu:

```
Plano: 6/6 shots, estimativa BRL 21.36 (até 29.42 com reparos)
  SHOT_002: SHOT_RECONSTRUCTION  CONTACT_SURFACE, CONTINUITY, GAZE_TARGET, PHYSICS_MOTION, ...
  SHOT_003: SHOT_RECONSTRUCTION  DERIVED_ENTITY, DESTRUCTION_FX, AUDIO_SFX, ...
   69.3%  Corrigindo SHOT_002: Prato desaparece entre 00:03.8 e 00:04.3 durante a ação. (tentativa 1/2)
Geração: COMPLETED — {"repairs": 2, "actualCost": 26.1852, "estimatedCost": 21.36, ...}
```

> Os custos acima são **fictícios**: vêm dos providers mock em
> [`apps/api/config/providers.yaml`](apps/api/config/providers.yaml) e servem para exercitar
> o roteador e o ledger de custos. Não descrevem nenhum serviço real.

Atrás de um proxy que intercepta TLS (rede corporativa, sandbox), o build precisa do CA do
proxy — ver [Docker](#docker).

## O que funciona hoje

| Área | Implementado |
|------|--------------|
| **Projetos** | criar, listar, renomear, duplicar (copia a mídia), excluir projeto ou só a mídia, locks e modo de qualidade por projeto |
| **Upload** | multipart com URLs assinadas por parte, retomável (status das partes), abortável; upload simples como alternativa; confirmação de direitos obrigatória; validação de tipo, tamanho, duração e codec por ffprobe |
| **Análise** | proxy 720p e poster, hash de conteúdo, detecção de shots (FFmpeg: scene score adaptativo + blackdetect), keyframes por shot, cores dominantes; camadas de IA via roteador (narrativa multimodal, detecção/OCR nos keyframes, tracking por shot, fala/áudio); consenso entre detector e modelo multimodal; elementos incertos marcados para revisão; reuso de análise para o mesmo conteúdo |
| **Video DNA** | schema versionado e validado (integridade referencial), DNA original imutável + DNA atual = original + operações; IDs persistentes (`CHARACTER_001`, `OBJECT_001`…) |
| **Editor** | árvore de elementos, player com caixas sobre o vídeo, timeline (shots, ações, áudio, QA), inspetor por elemento com Manter / Substituir / Remover / Alterar aparência, instrução personalizada, correção da análise, undo/redo, versões |
| **Sugestões** | cards contextuais por categoria (cabelo, cor, roupa, objeto, cenário…), "gerar mais opções", preview de frame da sugestão aplicada a um keyframe real |
| **Impacto** | nível (baixo/médio/alto), shots e elementos afetados, dependências (interação com a mão, física, quebra/fragmentos, olhar, contato, continuidade, iluminação, papel na história, efeito sonoro…), avisos de lock (ex.: LOCK STORY) |
| **Plano** | estratégia mais leve por shot (de *passthrough* a reconstrução), provider/modelo escolhido pelo roteador com justificativa, Character/Scene Reference Packs, custo estimado e teto com reparos, detecção de plano desatualizado |
| **Geração** | shot a shot, QA técnico (FFmpeg) + inspetor de IA, reparo localizado só na janela com problema, limite de tentativas por modo, guarda de orçamento, montagem com o áudio original, provenance JSON, versão criada automaticamente |
| **Resultado** | comparação original × modificado sincronizada, download, custos reais × estimados |
| **Plataforma** | jobs idempotentes com progresso por SSE e polling, cancelamento, Dramatiq + Redis, auth JWT, rate limit, URLs assinadas, retenção de mídia, métricas admin, registro de uso e custo por chamada de provider, feature flags |

## Arquitetura

```
          ┌──────────────────────── Next.js (apps/web) ─────────────────────────┐
          │ editor · sugestões · impacto · plano · progresso (SSE) · comparação │
          └───────────────┬─────────────────────────────────▲───────────────────┘
                REST + SSE│  client TS gerado do OpenAPI      │ PUT direto (URLs assinadas)
          ┌───────────────▼────────────── FastAPI (apps/api) ─┼───────────────────┐
          │ routes → services → domain (Video DNA, operações, impacto)            │
          │                    └→ jobs: create_job (idempotente) → fila           │
          └───────┬───────────────┬──────────────────────┬──────────┬────────────┘
                  │               │                      │          │
             PostgreSQL         Redis ◀── Dramatiq ── workers     S3 / MinIO
          (DNA, operações,     (fila)       │                    (vídeos, proxies,
           planos, jobs,                    ▼                     keyframes, saídas)
           custos, QA)         ┌──── AI Orchestrator ─────────────────────────┐
                               │ Gateway → Router (custo, qualidade, sucesso, │
                               │ latência, limites, saúde) → Adapter          │
                               │ timeout · retry · fallback · ProviderUsage   │
                               └──── mock / local (FFmpeg) / reais (futuro) ──┘
```

Decisões principais (detalhes em [docs/architecture-decisions](docs/architecture-decisions/)):

- **Monólito modular + workers** — um único pacote Python (`videodna`) com fronteiras
  claras (domain / services / orchestrator / media / storage / jobs / api); a mesma imagem
  roda a API e o worker. ([ADR-0001](docs/architecture-decisions/0001-modular-monolith-with-workers.md))
- **Video DNA em dois formatos** — JSON imutável (fonte da verdade, versionado) + linhas
  normalizadas para consulta. ([ADR-0002](docs/architecture-decisions/0002-video-dna-dual-storage.md))
- **Edição por operações** — o DNA atual é sempre `apply_operations(original, ativas)`;
  undo/redo e versões são só estados das operações. ([ADR-0003](docs/architecture-decisions/0003-operation-based-editing.md))
- **Nenhum código de negócio conhece um vendor** — pede-se uma *capability* ao roteador.
  ([ADR-0005](docs/architecture-decisions/0005-capability-router-and-adapters.md))
- **Nada caro sem plano** — o plano é congelado, mostra custo e precisa ser confirmado.
  ([ADR-0006](docs/architecture-decisions/0006-plan-before-generate.md))

Visão completa dos módulos e dos fluxos: [docs/architecture.md](docs/architecture.md).

## Estrutura do projeto

```
videodna-studio/
├── apps/
│   ├── api/                      # backend Python (FastAPI + workers)
│   │   ├── config/               # providers.yaml (registry), features.yaml (flags)
│   │   ├── migrations/           # Alembic
│   │   ├── src/videodna/
│   │   │   ├── api/              # app, rotas, schemas (camelCase), segurança, rate limit
│   │   │   ├── domain/           # Video DNA, operações, impacto, vocabulário — sem I/O
│   │   │   ├── services/         # projetos, upload, análise, edição, sugestões, geração
│   │   │   ├── orchestrator/     # capabilities, registry, router, gateway, adapters/
│   │   │   ├── media/            # ffprobe, shots, keyframes, transcode, cores
│   │   │   ├── storage/          # local (URLs assinadas pela API) e S3/MinIO/R2
│   │   │   ├── jobs/             # create/claim/cancel, eventos, fila (inline/thread/dramatiq)
│   │   │   ├── db/               # modelos SQLAlchemy 2.0
│   │   │   ├── fixtures/         # história do mock (boy_glass.json)
│   │   │   └── cli.py            # videodna worker | seed-demo | sample-video | ...
│   │   └── tests/
│   └── web/                      # Next.js 16 + React 19 + Tailwind 4
│       └── src/{app,components,lib}
├── packages/
│   └── api-client/               # openapi.json exportado + tipos TS gerados + client
├── infra/minio/                  # MinIO compilado do código-fonte (ver ADR-0009)
├── docs/                         # arquitetura, Video DNA, providers, segurança, ADRs
├── docker-compose.yml
├── Makefile                      # `make help`
└── .env.example
```

## Setup local (sem Docker)

Para quem vai **desenvolver** (para só usar, o caminho é o [Início rápido](#início-rápido)).

Pré-requisitos: **Python 3.11+** com [uv](https://docs.astral.sh/uv/), **Node 22+** com
pnpm (`npm install -g pnpm@10.28.0` — o `corepack` não vem mais em todas as versões do Node)
e **FFmpeg/FFprobe** no PATH. No Windows, use uma build GPL do FFmpeg, que inclui o `libx264`
usado nos proxies e nas saídas; confira com `ffmpeg -hide_banner -encoders | findstr libx264`.

```sh
cd videodna-studio
make install                       # uv sync + pnpm install
```

### Opção A — zero infraestrutura (SQLite, fila em thread, storage local)

Bom para experimentar e desenvolver o frontend; não precisa de Postgres, Redis nem MinIO.
A pasta `var/` é criada sozinha.

Linux/macOS:

```sh
cd apps/api
export DATABASE_URL=sqlite:///./var/videodna.db QUEUE_BACKEND=thread \
       STORAGE_BACKEND=local REDIS_URL=
uv run alembic upgrade head
uv run uvicorn videodna.main:app --reload --port 8000
```

Windows (PowerShell):

```powershell
cd apps\api
$env:DATABASE_URL = "sqlite:///./var/videodna.db"
$env:QUEUE_BACKEND = "thread"
$env:STORAGE_BACKEND = "local"
$env:REDIS_URL = ""
uv run alembic upgrade head
uv run uvicorn videodna.main:app --reload --port 8000
```

As variáveis `$env:` valem até fechar aquela janela do PowerShell — abra uma janela nova
para voltar à configuração padrão.

Em outro terminal: `pnpm --filter @videodna/web dev` e abra http://localhost:3000.

### Opção B — infraestrutura real em containers, código local

```sh
make infra                         # postgres:5432 e redis:6379 publicados no host
cp .env.example apps/api/.env      # STORAGE_BACKEND=local por padrão
make migrate
make api                           # terminal 1
make worker                        # terminal 2 (QUEUE_BACKEND=dramatiq)
make web                           # terminal 3
```

`make help` lista todos os atalhos (`seed`, `test`, `lint`, `typecheck`, `openapi`, `check`…).
`make infra-s3` sobe também o MinIO (portas 9000/9001) para testar `STORAGE_BACKEND=s3`.

No Windows não há `make`; os equivalentes da opção B no PowerShell:

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis
Copy-Item .env.example apps\api\.env
cd apps\api
uv run alembic upgrade head
uv run uvicorn videodna.main:app --reload --port 8000   # janela 1
uv run videodna worker                                  # janela 2
pnpm --filter @videodna/web dev                         # janela 3 (na pasta videodna-studio)
```

Ao editar o `.env` no Windows, salve como UTF-8 (o Bloco de Notas faz isso por padrão). Não
crie o arquivo com `echo ... > .env` no Windows PowerShell 5.1: ele grava em UTF-16 e o
arquivo deixa de ser lido.

## Docker

`docker compose up -d --build` (ou `.\iniciar.ps1` no Windows) sobe:

| Serviço    | Imagem                                    | Função |
|------------|-------------------------------------------|--------|
| `postgres` | `postgres:16-alpine`                      | banco (só na rede interna) |
| `redis`    | `redis:7-alpine`                          | broker da fila (só na rede interna) |
| `api`      | `videodna/api:local`                      | aplica migrations e sobe o uvicorn; healthcheck em `/healthz` |
| `worker`   | `videodna/api:local`                      | `videodna worker` (Dramatiq) — mesma imagem da API |
| `web`      | `videodna/web:local`                      | Next.js standalone |

Os vídeos ficam no volume `storage`, compartilhado entre API e worker; só as portas 3000
e 8000 são publicadas no host, para não colidir com um Postgres ou Redis já instalados.

Arquivos adicionais, combinados com `-f`:

| Arquivo | Para quê |
|---------|----------|
| `docker-compose.s3.yml` | storage S3 via MinIO (`STORAGE_BACKEND=s3`, upload direto do navegador para o bucket); console em http://localhost:9001 (`videodna` / `videodna-secret`) |
| `docker-compose.dev.yml` | publica Postgres (5432) e Redis (6379) no host, para rodar API/worker/web fora dos containers |

```sh
docker compose -f docker-compose.yml -f docker-compose.s3.yml up -d --build
```

Pontos que valem saber:

- **Sem `apt-get`** nas imagens: o FFmpeg vem de uma imagem estática
  (`mwader/static-ffmpeg`), as dependências Python do `uv.lock`, as do Node do
  `pnpm-lock.yaml`. Os builds são reprodutíveis e não dependem de espelhos do Debian.
- **MinIO é compilado do código-fonte** (`infra/minio/Dockerfile`), numa versão fixada, e
  roda sobre distroless — por isso fica fora do stack padrão: compilar exige baixar os
  módulos Go e alguns minutos de CPU. O MinIO deixou de publicar imagens de container para a
  comunidade; em produção use AWS S3 ou Cloudflare R2 (só muda `S3_*`). Ver
  [ADR-0009](docs/architecture-decisions/0009-minio-built-from-source.md).
- **Proxy com interceptação TLS:** os Dockerfiles aceitam um *build secret* opcional `ca`.
  Aponte `EXTRA_CA_CERT` para o certificado do proxy antes do build:
  ```sh
  EXTRA_CA_CERT=/caminho/proxy-ca.pem docker compose build
  ```
  No PowerShell: `$env:EXTRA_CA_CERT = "C:\caminho\proxy-ca.pem"` antes do `iniciar.ps1`.
  Sem a variável, um arquivo vazio (`infra/no-extra-ca.pem`) é usado e nada muda.
- **Rede instável no primeiro build** (`DeadlineExceeded`, `TLS handshake timeout`,
  `i/o timeout` ao falar com `registry-1.docker.io`): o `docker compose` resolve as imagens
  base de todos os serviços ao mesmo tempo e desiste rápido. O `iniciar.ps1` baixa uma de
  cada vez com novas tentativas; fora do Windows, `docker pull` de cada imagem base antes do
  build tem o mesmo efeito. Reiniciar o Docker Desktop e desligar VPN resolve a maioria dos
  casos de DNS.
- **URLs assinadas e o host:** dentro do compose o MinIO é `minio:9000`, mas o navegador
  precisa de `localhost:9000` — por isso existem `S3_ENDPOINT_URL` (servidor) e
  `S3_PUBLIC_ENDPOINT_URL` (o que vai nas URLs assinadas).
- `NEXT_PUBLIC_API_URL` é embutida no build do web; mudou o host da API, refaça o build.

## Variáveis de ambiente

Todas estão documentadas em [`.env.example`](.env.example) (backend) e
[`apps/web/.env.example`](apps/web/.env.example) (frontend — só a URL da API). As mais
importantes:

| Variável | Padrão | Para quê |
|----------|--------|----------|
| `APP_ENV` | `development` | `production` recusa segredos padrão e autologin |
| `DATABASE_URL` | Postgres local | também aceita `sqlite:///...` |
| `QUEUE_BACKEND` | `dramatiq` | `thread` (dev sem Redis) ou `inline` (testes) |
| `STORAGE_BACKEND` | `local` | `s3` para S3/R2/MinIO |
| `AI_MOCK_MODE` | `true` | só providers mock/locais; nenhum crédito gasto |
| `JWT_SECRET`, `SIGNING_SECRET` | inseguro (dev) | **obrigatórios** em produção |
| `AUTH_DEV_AUTOLOGIN` | `true` | requisição sem token = usuário dev; proibido em produção |
| `FEATURE_FLAGS` | vazio | `smart_mode=true,provider.mock-v2v=false` |
| `COST_CURRENCY`, `FX_RATES_TO_BASE` | `BRL`, vazio | moeda do produto e câmbio que **você** define |
| `MEDIA_RETENTION_DAYS` | `30` | prazo de retenção da mídia enviada |

Listas (`CORS_ORIGINS`, `UPLOAD_ALLOWED_CONTENT_TYPES`, `VIDEO_ALLOWED_CODECS`) aceitam
`a,b,c` ou JSON. Segredos são `SecretStr` e nunca aparecem em logs.

## Mock mode

`AI_MOCK_MODE=true` (padrão) é um modo de produto completo, não um atalho de teste:

- Tudo que é **determinístico roda de verdade**: ffprobe, proxy, detecção de shots,
  keyframes, cores, QA técnico, cortes, splice, concat, mux do áudio.
- As **camadas de IA** são providers mock registrados como qualquer outro, com custo,
  latência, qualidade e limites fictícios. O roteador escolhe entre eles do mesmo jeito que
  escolherá entre providers reais.
- A análise usa a história de fixture [`boy_glass.json`](apps/api/src/videodna/fixtures/stories/boy_glass.json)
  mapeada sobre os shots **realmente detectados** no vídeo enviado. O detector mock discorda
  de propósito do modelo multimodal em dois elementos ("Taça?", "Pufe?") para exercitar o
  consenso e a revisão de elementos incertos.
- A "geração" desenha as alterações sobre o vídeo original com FFmpeg (caixas seguindo os
  tracks, ajuste de cor, selo do shot), para que o resultado seja visualmente comparável.
- O inspetor de QA mock reporta, na primeira tentativa, o objeto físico desaparecendo
  durante a ação — o que dispara o **reparo localizado** e mostra o ciclo completo.
- `MOCK_PROVIDER_FAILURES="mock-edit-pro:error"` injeta falhas para testar retry e fallback.

Com `AI_MOCK_MODE=false`, providers mock ficam indisponíveis e só providers reais (ou
locais) são roteados — hoje isso significa que as etapas de IA ficam sem provider até que
o primeiro adapter real seja adicionado.

## Workers e jobs

- Todo trabalho pesado (ingestão, análise, preview de frame, geração) é um **Job** no banco.
  `create_job` é idempotente por `(projeto, tipo, idempotency_key)`: repetir o POST devolve o
  mesmo job (o frontend envia `Idempotency-Key`).
- O worker faz um *claim* atômico (`QUEUED → PREPARING`), então duas entregas da mesma
  mensagem não rodam o job duas vezes.
- Cada etapa grava um `JobEvent`; o frontend acompanha por **SSE**
  (`GET /jobs/{id}/events`) ou polling (`/events/history`). Cancelar é cooperativo
  (`POST /jobs/{id}/cancel`): o job para no próximo checkpoint.
- Filas: `dramatiq` (Redis, produção), `thread` (na própria API, dev) e `inline` (testes).

```sh
uv run videodna worker --processes 1 --threads 2
```

## Banco de dados

PostgreSQL 16 com SQLAlchemy 2.0 (modelos tipados) e Alembic. 21 tabelas: usuários,
projetos, vídeos, análises, cenas, shots, entidades (herança de tabela única por tipo),
tracks, ações, relações, operações de edição, sugestões, planos, jobs, eventos de job,
saídas, relatórios e issues de QA, versões, uso de provider e lançamentos de custo.
Colunas JSON viram JSONB no Postgres.

```sh
make migrate                                     # alembic upgrade head
cd apps/api && uv run alembic revision --autogenerate -m "..."   # nova migration
```

Os testes rodam em SQLite por padrão e em Postgres com `TEST_DATABASE_URL`.

## Storage

Uma interface (`storage/base.py`) e dois backends:

- **local** — arquivos em `STORAGE_LOCAL_ROOT`; downloads e uploads passam por URLs
  assinadas (HMAC com `SIGNING_SECRET`, expiração) servidas pela própria API, com suporte
  a `Range` para o player.
- **s3** — AWS S3, Cloudflare R2 ou MinIO. Upload **multipart direto do navegador** com uma
  URL assinada por parte (o arquivo não passa pela API), retomável via
  `GET /projects/{id}/uploads/{uploadId}`.

Chaves seguem `projects/<id>/...`, o que permite excluir toda a mídia de um projeto. A
limpeza de mídia vencida roda com `uv run videodna cleanup-media`.

## Providers de IA

O registro fica em [`apps/api/config/providers.yaml`](apps/api/config/providers.yaml). Cada
provider declara tipo, capabilities, recursos (máscara, referências, preservação de
câmera/movimento, faixa parcial…), qualidade, custo, limites, latência, modelos, a URL da
documentação oficial e o **nome** das variáveis de ambiente com suas credenciais.

O roteador pontua os candidatos disponíveis por modo de qualidade:

| Modo | custo | qualidade | sucesso | latência | piso de qualidade |
|------|------:|----------:|--------:|---------:|------------------:|
| `ECONOMY` | 0.55 | 0.20 | 0.20 | 0.05 | — |
| `BALANCED` | 0.30 | 0.40 | 0.20 | 0.10 | 0.70 |
| `MAX` | 0.02 | 0.70 | 0.25 | 0.03 | 0.80 |

O custo considerado é o **custo efetivo** (preço ÷ taxa de sucesso); a taxa de sucesso
combina um *prior* com o histórico real de `ProviderUsage`. Falhas transitórias têm retry
com backoff; erro de cota/indisponibilidade cai para o próximo candidato, desde que o
fallback não custe mais que `FALLBACK_MAX_COST_INCREASE`.

**Para adicionar um provider real** siga o checklist de
[docs/providers.md](docs/providers.md): ler a documentação oficial, copiar limites e preços
de lá (com a data da consulta), implementar a interface do tipo (`VideoEditorProvider`,
`QAProvider`…), declarar `docs_url` e `credentials_env`, escrever o teste de contrato do
adapter. O carregamento recusa provider real sem `docs_url`, e o registry o deixa
indisponível enquanto faltar alguma credencial.

## API

FastAPI com OpenAPI em `/docs` e `/openapi.json`. Respostas em camelCase; erros sempre no
formato `{"error": {"code", "message", "details", "requestId"}}` com mensagens em
português. Principais grupos:

| Grupo | Endpoints |
|-------|-----------|
| Saúde/config | `GET /healthz`, `GET /readyz`, `GET /config`, `GET /providers` |
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Projetos | `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}`, `DELETE /projects/{id}/media`, `POST /projects/{id}/duplicate` |
| Upload | `POST /projects/{id}/uploads`, `GET/DELETE /projects/{id}/uploads/{uploadId}`, `POST .../complete`, `POST /projects/{id}/upload` |
| Análise | `POST /projects/{id}/analyze`, `GET /projects/{id}/analysis`, `GET /projects/{id}/video-dna?view=original\|current`, `GET /projects/{id}/entities`, `GET/PATCH /entities/{id}` |
| Edição | `GET/POST /projects/{id}/edits`, `POST /projects/{id}/impact`, `DELETE .../edits/{editId}`, `POST .../edits/undo`, `POST .../edits/redo` |
| Sugestões | `GET /entities/{id}/suggestions`, `POST /entities/{id}/suggestions/more`, `POST /suggestions/{id}/apply`, `POST /suggestions/{id}/preview` |
| Geração | `POST /projects/{id}/generation-plan`, `POST /projects/{id}/cost-estimate`, `GET .../generation-plans/{planId}`, `POST /projects/{id}/generate`, `GET /projects/{id}/outputs`, `GET /outputs/{id}`, `GET /jobs/{id}/qa`, `GET /projects/{id}/costs` |
| Jobs | `GET /jobs/{id}`, `GET /jobs/{id}/events` (SSE), `GET /jobs/{id}/events/history`, `POST /jobs/{id}/cancel`, `GET /projects/{id}/jobs` |
| Versões | `GET/POST /projects/{id}/versions`, `POST .../versions/{versionId}/restore` |
| Admin | `GET /admin/metrics` |

O client TypeScript (`packages/api-client`) é gerado do contrato: `make openapi` exporta o
`openapi.json` e regenera `schema.d.ts`. Mudou um schema no backend, rode e faça commit dos
dois arquivos.

## Frontend

Next.js 16 (App Router, Turbopack, `output: standalone`), React 19, Tailwind 4 (tema escuro
de estúdio), TanStack Query para dados do servidor, Zustand para o estado do editor,
`openapi-fetch` com os tipos gerados.

| Tela | Rota |
|------|------|
| Projetos | `/` |
| Novo projeto + upload | `/projects/new` |
| Análise (progresso) e editor | `/projects/[id]` |
| Revisar alterações e plano | `/projects/[id]/review` |
| Progresso da geração | `/projects/[id]/jobs/[jobId]` |
| Resultado e comparação | `/projects/[id]/result` |
| Login / Admin | `/login`, `/admin` |

O editor tem atalhos `Ctrl+Z` / `Ctrl+Shift+Z`, mostra as caixas dos elementos sobre o
vídeo, e cada alteração exibe o card de impacto antes de ser aplicada.

## Testes

```sh
make test                  # backend + frontend
make test-api              # pytest (SQLite)
TEST_DATABASE_URL=postgresql+psycopg://videodna:videodna@localhost:5432/videodna_test \
  make test-api            # mesmos testes em Postgres
make lint typecheck        # ruff, eslint, tsc
make check                 # lint + tipos + testes + build do web
```

| Suite | Cobre |
|-------|-------|
| `test_domain.py` | schema do DNA, operações, undo/redo, impacto e dependências, vocabulário |
| `test_orchestrator.py` | contrato de todos os adapters, registry, roteamento por modo, custo efetivo, fallback, timeout/retry, credenciais |
| `test_flow_analysis.py` | upload → análise → DNA de ponta a ponta com FFmpeg real, reuso, validação de mídia |
| `test_flow_generation.py` | sugestões, impacto, plano, geração mock, QA, reparo, montagem e o caso §79 completo |
| `test_platform.py` | jobs (idempotência, claim, cancelamento, SSE), segurança, S3 (moto), migrations, splice, admin, configuração |
| `apps/web/src/lib/lib.test.ts` | utilitários do frontend (formatação, DNA, SSE) |

## Segurança, privacidade e uso responsável

- Chaves de providers **só no servidor**, lidas de variáveis de ambiente declaradas em
  `credentials_env`; o frontend nunca as recebe. Nenhum segredo é versionado.
- Produção recusa segredos padrão e autologin. JWT para auth, rate limit por usuário
  (mais restrito em rotas caras), URLs assinadas com expiração, validação de mídia por
  ffprobe (não pela extensão), limites de tamanho e duração.
- Cada projeto pertence a um usuário; todas as consultas filtram pelo dono.
- O upload exige a **confirmação de direitos** sobre o vídeo, registrada com data e texto.
- Retenção configurável, exclusão de projeto ou só da mídia, `cleanup-media` para o vencido.
- O resultado leva um **provenance JSON** (vídeo de origem, plano, operações, providers,
  modo mock) e os metadados do container são limpos na montagem.
- O projeto não implementa nada cujo objetivo seja enganar sistemas de autoria, fingerprint
  ou detecção de conteúdo gerado.

Detalhes: [docs/security-privacy.md](docs/security-privacy.md).

## Limitações conhecidas e roadmap

- **Nenhum provider de IA real** está implementado. O próximo passo é a slice 4: escolher
  providers por capability, ler a documentação e os preços oficiais, e escrever os
  adapters (o checklist está em [docs/providers.md](docs/providers.md)).
- As flags `smart_mode`, `auto_mode`, `advanced_editing`, `experimental_analysis`,
  `ai_consensus` e `audio_regeneration` existem em `features.yaml` mas as funcionalidades
  correspondentes ainda não foram construídas (MVPs seguintes). `frame_previews` está ativa.
- A análise mock sempre conta a mesma história (menino/copo/mãe), mapeada sobre os shots
  reais do vídeo enviado.
- Áudio: o original é preservado (LOCK AUDIO); regenerar efeitos sonoros é recurso futuro —
  o plano já sinaliza a dependência `AUDIO_SFX` quando ela existe.
- Um único worker processa um shot por vez dentro de um job; paralelizar shots entre
  workers é uma evolução natural do runner.

## Documentação adicional

- [docs/architecture.md](docs/architecture.md) — módulos, fluxos de análise e geração, modelo de dados
- [docs/video-dna.md](docs/video-dna.md) — schema do Video DNA, operações, impacto e dependências
- [docs/providers.md](docs/providers.md) — registry, roteamento e como adicionar um provider real
- [docs/security-privacy.md](docs/security-privacy.md) — segurança, privacidade, direitos e retenção
- [docs/architecture-decisions/](docs/architecture-decisions/) — ADRs
- [apps/api/README.md](apps/api/README.md) — comandos do backend
