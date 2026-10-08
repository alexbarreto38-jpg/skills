# 0003 — Edição como operações sobre o DNA original

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

O usuário edita o DNA (troca roupa, objeto, cenário), precisa de undo/redo, de versões, e
o plano de geração precisa saber exatamente quais alterações foram pedidas. Editar o DNA
no lugar perderia o original e tornaria undo e versões frágeis.

## Decisão

Cada alteração é uma `EditOperation` (`SET_ATTRIBUTE`, `REPLACE`, `REMOVE`, `KEEP`,
`APPLY_PRESET`, `ADD_ENTITY`, `CORRECT`, `CHANGE_APPEARANCE`, `INSTRUCTION`) com
sequência e status (`ACTIVE`, `UNDONE`, `DISCARDED`). O DNA atual é sempre
`apply_operations(original, operações ACTIVE em ordem)`, uma função pura em
`domain/operations.py`.

- Undo: a última ativa vira `UNDONE`. Redo: a mais antiga desfeita volta a `ACTIVE`.
- Nova operação com desfeitas pendentes: as desfeitas viram `DISCARDED`.
- Versão: uma cópia nomeada das operações ativas. Restaurar descarta as atuais e recria as
  da versão como novas operações ativas — a própria restauração entra no histórico.
- Remover uma operação específica (`DELETE /edits/{id}`) a descarta; se ela adicionou um
  elemento, as edições feitas nesse elemento são descartadas junto.
- O plano congela as operações e guarda um fingerprint delas.

## Alternativas consideradas

- **Snapshots do DNA a cada edição** — simples para undo, mas multiplica o armazenamento,
  e o plano perderia o "o que mudou" (teria que diferenciar documentos).
- **Event sourcing completo com projeções persistidas** — mais infraestrutura do que o
  problema pede; o DNA de um vídeo é pequeno o bastante para ser recalculado.

## Consequências

- Undo/redo e versões são atualizações de status, baratas e sem perda.
- O impacto de cada operação é calculado contra o original e o atual, então o card de
  impacto e o plano falam a mesma língua.
- `apply_operations` precisa ser determinística e rápida; é coberta por testes de domínio.
- O ID de um elemento adicionado (`OBJECT_101`…) é fixado na operação no momento em que
  ela é criada (`newValue.entityKey`). Recalculá-lo a cada replay renumeraria os elementos
  adicionados depois quando um anterior fosse removido, e as edições feitas neles mudariam
  de alvo em silêncio.
