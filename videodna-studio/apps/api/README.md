# videodna (backend)

API FastAPI, AI Orchestrator, pipelines de análise/geração e workers do VideoDNA Studio.

A documentação completa (setup, arquitetura, providers, testes) está no
[README da raiz do projeto](../../README.md) e em [`docs/`](../../docs/).

Comandos rápidos (a partir deste diretório):

```sh
uv sync                                   # instala dependências
uv run alembic upgrade head               # aplica migrations
uv run uvicorn videodna.main:app --reload # API em http://localhost:8000/docs
uv run videodna worker                    # worker (Dramatiq + Redis)
uv run pytest                             # testes
```
