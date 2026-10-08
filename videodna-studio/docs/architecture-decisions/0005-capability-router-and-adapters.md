# 0005 — Capabilities, registry, router e adapters por provider

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

O mercado de modelos de vídeo muda mês a mês: surgem fornecedores, preços mudam, modelos
são descontinuados. A especificação exige não ficar preso a um fornecedor, escolher o
provider por custo e qualidade conforme o modo (Econômico / Equilibrado / Máximo), ter
fallback, e nunca inventar API ou preço.

## Decisão

- O código de negócio pede uma **capability** (`video.localized_edit`,
  `qa.video_inspection`…), nunca um fornecedor.
- Dez **interfaces** por tipo de provider (`orchestrator/interfaces.py`) com modelos de
  request/response próprios do VideoDNA.
- Um **registro declarativo** (`config/providers.yaml`) descreve cada provider: tipo,
  capabilities, recursos, qualidade, custo, limites, latência, modelos, `docs_url`,
  `credentials_env`. Validado no carregamento.
- Um **roteador** filtra por disponibilidade e pontua por custo efetivo, qualidade, taxa de
  sucesso (prior + histórico próprio) e latência, com pesos por modo e piso de qualidade, e
  devolve a decisão **com justificativa** — o plano a exibe.
- Um **gateway** aplica timeout, retry com backoff, um fallback com teto de custo, e grava
  `provider_usage` e `cost_entries` de cada tentativa.

## Alternativas consideradas

- **SDK de um fornecedor direto nos serviços** — rápido no começo, caro para sair depois,
  e impede comparar fornecedores no mesmo plano.
- **Biblioteca genérica de roteamento de LLM** — resolve texto; não conhece recursos de
  vídeo (máscara, faixa parcial, preservação de câmera) nem custo por segundo de vídeo.

## Consequências

- Adicionar um fornecedor é escrever um adapter e uma entrada no YAML; nada no planner,
  runner ou API muda.
- Provider real exige `docs_url` (o carregamento recusa sem) e fica indisponível enquanto
  faltar uma credencial de `credentials_env`.
- As notas de qualidade precisam vir de avaliação própria; o roteador é tão bom quanto os
  números do registro, por isso o histórico real de sucesso pesa cada vez mais.
- Os mocks registrados têm perfis diferentes para que o roteamento seja exercitado de
  verdade em `AI_MOCK_MODE` (ADR-0008).
