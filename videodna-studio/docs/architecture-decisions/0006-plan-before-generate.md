# 0006 — Nada caro sem plano congelado e confirmado

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

Geração de vídeo por IA custa caro e demora. A especificação proíbe disparar geração cara
sem confirmação e pede que o usuário veja, antes, o que será feito, com qual provider e
quanto custa — e que o sistema use a estratégia mais leve possível por shot.

## Decisão

1. `POST /generation-plan` cria um **Generation Plan**: impacto de cada operação → shots
   afetados → estratégia mais leve viável por shot (`PASSTHROUGH` … `FULL_REGENERATION`) →
   provider/modelo escolhido pelo roteador → custo estimado e teto com reparos.
2. O plano é **congelado**: guarda as operações e um fingerprint (análise + operações +
   modo + resolução + locks).
3. `POST /generate` exige um `planId`; se o projeto mudou desde o plano, o plano está
   desatualizado e a geração é recusada. `Idempotency-Key` evita execução duplicada.
4. Durante a execução, um **guarda de orçamento** impede reparos pagos quando o gasto real
   passa do estimado + tolerância.

## Alternativas consideradas

- **Gerar direto a partir das edições** — sem visão de custo, sem chance de escolher o
  modo, e qualquer edição posterior durante a execução tornaria o resultado ambíguo.
- **Plano só informativo, recalculado na execução** — o que o usuário aprovou poderia não
  ser o que roda.

## Consequências

- Shots sem alteração são copiados do original sem custo — normalmente a maior economia.
- A tela de revisão mostra estratégia, provider, dependências e custo por shot; o usuário
  pode trocar o modo e a resolução (preview 720p / final 1080p) antes de confirmar.
- Planejar é barato (sem chamadas a provider), então pode ser refeito à vontade.
