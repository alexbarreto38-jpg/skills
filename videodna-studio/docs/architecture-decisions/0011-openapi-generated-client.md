# 0011 — Client TypeScript gerado do OpenAPI

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

O frontend consome ~50 endpoints com payloads ricos (Video DNA, impacto, plano). Tipos
escritos à mão divergem do backend em silêncio.

## Decisão

- O FastAPI é a fonte do contrato. `videodna export-openapi` grava
  `packages/api-client/openapi.json`; `openapi-typescript` gera `src/schema.d.ts`; o
  frontend usa `openapi-fetch` tipado por esse schema. `make openapi` faz os dois passos.
- Schemas da API usam camelCase (`alias_generator`) e
  `json_schema_serialization_defaults_required=True`, para que campos com default
  apareçam como obrigatórios **na resposta** e opcionais **na requisição** — o TypeScript
  reflete exatamente o que o servidor envia.
- Os dois arquivos gerados são versionados: a revisão de uma PR mostra a mudança de
  contrato.

## Alternativas consideradas

- **Tipos manuais** — divergem.
- **Gerar um SDK completo com classes** — mais código gerado para revisar sem ganho sobre
  `openapi-fetch` + tipos.
- **tRPC/GraphQL** — trocaria o backend Python por outro ecossistema ou acrescentaria uma
  camada.

## Consequências

- Mudou um schema no backend: rode `make openapi` e faça commit dos dois arquivos; o
  `tsc` acusa no frontend tudo que quebrou.
- Modelos usados tanto em entrada quanto em saída aparecem com sufixos `-Input`/`-Output`
  no schema gerado; `packages/api-client/src/index.ts` expõe aliases com nomes estáveis.
