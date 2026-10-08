# 0004 — Herança de tabela única para entidades e jobs

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

A especificação pede tipos distintos de elemento (personagem, cabelo, roupa, acessório,
objeto, móvel, ambiente, parte de ambiente, iluminação, texto, áudio) e de job (ingestão,
análise, preview, geração). Os tipos compartilham quase todos os campos e são consultados
juntos (a árvore do editor lista todos os elementos de um projeto; a fila lista todos os
jobs). O que varia entre eles são atributos livres (`attributes`) e o payload do job.

## Decisão

Uma tabela `entities` com discriminador `type` e uma tabela `jobs` com discriminador
`kind`, mapeadas com `polymorphic_on` no SQLAlchemy. Cada tipo tem sua subclasse
(`Character`, `Wardrobe`, `SceneObject`…, `AnalysisJob`, `GenerationJob`…) para dar nome
e comportamento no código, sem tabela própria. Atributos específicos ficam em JSON.

## Alternativas consideradas

- **Tabela por tipo (joined inheritance)** — onze joins para montar a árvore do editor,
  migrations a cada atributo novo de um tipo, e o ganho (colunas tipadas por tipo) é pequeno
  quando os atributos vêm de modelos de IA e variam de vídeo para vídeo.
- **Uma tabela sem subclasses** — funciona, mas espalha `if type == ...` pelo código.

## Consequências

- Listar e filtrar é uma consulta só; o índice `(project_id, type)` cobre a árvore do editor.
- Atributos por tipo não têm restrição de schema no banco — a validação fica no modelo
  pydantic do Video DNA, que é a fonte da verdade (ADR-0002).
- Novo tipo de elemento = novo valor no enum + subclasse, sem migration de tabela.
