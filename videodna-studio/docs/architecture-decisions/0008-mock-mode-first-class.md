# 0008 — Mock mode como modo de produto completo

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

Os providers reais ainda não foram escolhidos, cada chamada custa dinheiro, e a
especificação pede que a plataforma inteira seja desenvolvida e testada antes, com
`AI_MOCK_MODE`. Um mock que só devolve JSON fixo não exercitaria roteamento, custo, QA,
reparo nem a interface com vídeos de verdade.

## Decisão

- Providers mock são **providers registrados como quaisquer outros**, com perfis distintos
  de custo, qualidade, limites e recursos (valores fictícios, marcados como tal). O
  roteador e o planejador tomam decisões reais entre eles.
- Tudo que é determinístico **roda de verdade** em mock mode: ffprobe, proxy, shots,
  keyframes, cores, QA técnico, corte, splice, concat, mux.
- A análise mock aplica uma história de fixture sobre os **shots realmente detectados**
  do vídeo enviado; o detector mock discorda do modelo multimodal em dois elementos para
  exercitar consenso e revisão.
- A geração mock **desenha** as alterações sobre o vídeo com FFmpeg (caixas nos tracks,
  cor, selo), e o inspetor mock reporta um problema de física na primeira tentativa, para
  que o reparo localizado aconteça.
- `AI_MOCK_MODE=true` desliga providers reais; `false` desliga os mocks. Locais valem nos
  dois. A interface mostra o selo "MOCK MODE".
- `MOCK_PROVIDER_FAILURES` injeta falhas por provider para testar retry e fallback.

## Alternativas consideradas

- **Mocks só nos testes (monkeypatch)** — a aplicação real não poderia ser usada nem
  demonstrada sem créditos, e o caminho de produção (registry → router → gateway) não
  seria exercitado.
- **Gravar respostas de um provider real e reproduzir** — exigiria escolher o fornecedor
  antes da hora e não cobre vídeos novos.

## Consequências

- O produto inteiro roda localmente sem nenhuma chave, inclusive na CI.
- O caminho de código em mock e em produção é o mesmo; só o adapter muda.
- A análise mock sempre conta a mesma história — mapeada sobre os cortes do vídeo, mas a
  mesma. Isso é aceitável para desenvolver e demonstrar e é dito na documentação.
