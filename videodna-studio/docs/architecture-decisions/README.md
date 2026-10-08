# Architecture Decision Records

Cada ADR registra uma decisão que molda o sistema: o contexto, o que foi decidido, as
alternativas descartadas e o preço que se paga. Uma decisão revista ganha um ADR novo que
*substitui* o anterior — os antigos não são reescritos.

| # | Decisão | Status |
|---|---------|--------|
| [0001](0001-modular-monolith-with-workers.md) | Monólito modular com workers, uma imagem para API e worker | Aceito |
| [0002](0002-video-dna-dual-storage.md) | Video DNA: JSON imutável + linhas normalizadas | Aceito |
| [0003](0003-operation-based-editing.md) | Edição como operações sobre o DNA original | Aceito |
| [0004](0004-single-table-inheritance.md) | Herança de tabela única para entidades e jobs | Aceito |
| [0005](0005-capability-router-and-adapters.md) | Capabilities, registry, router e adapters por provider | Aceito |
| [0006](0006-plan-before-generate.md) | Nada caro sem plano congelado e confirmado | Aceito |
| [0007](0007-jobs-in-database-dramatiq-sse.md) | Jobs no banco, Dramatiq + Redis, progresso por SSE | Aceito |
| [0008](0008-mock-mode-first-class.md) | Mock mode como modo de produto completo | Aceito |
| [0009](0009-minio-built-from-source.md) | MinIO compilado do código-fonte para desenvolvimento | Aceito |
| [0010](0010-storage-abstraction-signed-urls.md) | Storage abstrato, upload direto com URLs assinadas | Aceito |
| [0011](0011-openapi-generated-client.md) | Client TypeScript gerado do OpenAPI | Aceito |
| [0012](0012-local-first-analysis.md) | Análise em camadas: local primeiro, IA só no necessário | Aceito |

Modelo: [template.md](template.md).
