# VideoDNA Studio — atalhos de desenvolvimento. `make help` lista os alvos.
#
# Pré-requisitos locais: uv, pnpm (via corepack), node >= 22, ffmpeg/ffprobe.
# Para o stack completo em containers basta Docker: `make up`.
# No Windows (sem make): powershell -ExecutionPolicy Bypass -File .\iniciar.ps1

API := apps/api
UV := cd $(API) && uv run
# Mesma versão fixada em apps/api/package.json e no pre-commit do repositório.
RUFF := uvx ruff@0.14.13

.DEFAULT_GOAL := help
.PHONY: help install infra infra-s3 up up-s3 down logs migrate api worker web seed sample-video \
	test test-api test-web lint lint-api lint-web typecheck build openapi check fix

## help: lista os alvos
help:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  /'

## install: instala dependências Python (uv) e Node (pnpm)
install:
	cd $(API) && uv sync
	pnpm install

COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_S3 := docker compose -f docker-compose.yml -f docker-compose.s3.yml

## infra: sobe só postgres e redis, publicados no host (para rodar API/web fora de containers)
infra:
	$(COMPOSE_DEV) up -d postgres redis

## infra-s3: como infra, mais o MinIO em :9000/:9001 (para STORAGE_BACKEND=s3)
infra-s3:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.s3.yml up -d postgres redis minio

## up: sobe o stack completo (postgres, redis, api, worker, web) com storage local
up:
	docker compose up -d --build

## up-s3: sobe o stack completo com storage S3 (MinIO compilado na primeira vez)
up-s3:
	$(COMPOSE_S3) up -d --build

## down: derruba o stack (os volumes são mantidos; use `docker compose down -v` para apagar)
down:
	$(COMPOSE_S3) down --remove-orphans

## logs: acompanha os logs da API e do worker
logs:
	docker compose logs -f api worker

## migrate: aplica as migrations no DATABASE_URL atual
migrate:
	$(UV) alembic upgrade head

## api: API FastAPI com reload em http://localhost:8000/docs
api:
	$(UV) uvicorn videodna.main:app --reload --port 8000

## worker: worker Dramatiq (precisa de Redis e QUEUE_BACKEND=dramatiq)
worker:
	$(UV) videodna worker

## web: frontend Next.js em http://localhost:3000
web:
	pnpm --filter @videodna/web dev

## seed: cria o projeto de demonstração (spec §79) e gera o resultado mock
seed:
	$(UV) videodna seed-demo --generate

## sample-video: escreve o vídeo sintético de teste em var/sample.mp4
sample-video:
	$(UV) videodna sample-video ../../var/sample.mp4

## test: todos os testes (backend + frontend)
test: test-api test-web

test-api:
	$(UV) pytest

test-web:
	pnpm --filter @videodna/web test

## lint: ruff (backend) + eslint (frontend)
lint: lint-api lint-web

lint-api:
	$(RUFF) check . && $(RUFF) format --check .

lint-web:
	pnpm --filter @videodna/web lint

## typecheck: TypeScript (web + api-client)
typecheck:
	pnpm -r typecheck

## build: build de produção do frontend
build:
	pnpm --filter @videodna/web build

## openapi: exporta o contrato da API e regenera o client TypeScript
openapi:
	pnpm gen:api

## check: o que a CI deveria rodar — lint, tipos, testes e build
check: lint typecheck test build

## fix: aplica a formatação do ruff
fix:
	$(RUFF) check --fix . && $(RUFF) format .
