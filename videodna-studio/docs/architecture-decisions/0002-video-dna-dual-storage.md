# 0002 — Video DNA: JSON imutável + linhas normalizadas

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

O Video DNA é ao mesmo tempo um **documento** (precisa ser versionado, comparado,
reproduzido e entregue inteiro ao planejador) e um **conjunto de registros** consultados
individualmente (o editor lista entidades, filtra por shot, abre um elemento).

## Decisão

Gravar os dois:

1. `video_analyses.dna` — o DNA original completo, validado pelo schema pydantic
   (`schemaVersion`), em JSON/JSONB. **Nunca é alterado** depois de gravado.
2. Tabelas normalizadas (`scenes`, `shots`, `entities`, `entity_tracks`, `actions`,
   `relationships`) com os mesmos dados, para consulta e para chaves estrangeiras
   (operações, sugestões e issues de QA apontam para entidades e shots reais).

O DNA *atual* não é gravado: é derivado das operações (ADR-0003).

## Alternativas consideradas

- **Só JSON** — consultas por entidade/shot virariam varreduras de JSON e não haveria
  integridade referencial para operações e sugestões.
- **Só tabelas** — reconstruir o documento a cada leitura, sem uma fotografia imutável do
  que a análise produziu, dificulta reprodutibilidade e auditoria.

## Consequências

- A análise grava os dois numa transação; a persistência (`services/analysis/persistence.py`)
  é o único lugar que faz o mapeamento.
- Mudar o schema do DNA exige subir `schemaVersion` e, se as tabelas mudarem, uma migration.
- O reuso de análise (mesmo hash de conteúdo) copia o documento e regrava as linhas.
