# Video DNA

O Video DNA é a representação estruturada de um vídeo: o que existe nele, onde, quando, o
que acontece e como as coisas se relacionam. É o contrato entre a análise, o editor, o
planejador e a geração. Schema: `apps/api/src/videodna/domain/video_dna.py`
(versão `1.0`, campo `schemaVersion`).

## Estrutura

```
VideoDNA
├── technical          duração, fps, resolução, codecs, áudio, keyframes do codec
├── scenes[]           SCENE_001 … — intervalo, shots, ambiente, resumo
├── shots[]            SHOT_001 … — tempo/frames, transição, câmera, luz, cores, keyframes
├── entities[]         CHARACTER_001, HAIR_001, WARDROBE_001, OBJECT_001, ENVIRONMENT_001 …
├── tracks[]           TRACK_0001 … — amostras de bbox por frame, visibilidade, oclusão
├── actions[]          ACTION_001 … — verbo, ator, alvos, intervalo, física, resultado
├── relationships[]    REL_001 … — grafo de cena: sujeito, predicado, objeto, intervalo
├── narrative          resumo, beats, papéis (PERSONAGEM_A, OBJETO_A…)
├── audio              fala, música, efeitos, segmentos
├── onScreenText[]     legendas, placas, logos (nunca alterados automaticamente)
└── analysis           versão do pipeline, modo mock, providers usados, avisos
```

O modelo é estrito (`extra="forbid"`) e um validador confere a integridade referencial:
todo `parentId`, `shotIds`, `actorId`, `subjectId`, `trackIds`… precisa existir. Um DNA que
não valida não é salvo.

### Entidades

Hierárquicas: cabelo, roupas e acessórios têm `parentId` no personagem; janela, parede e
piso têm `parentId` no ambiente. Cada entidade traz `importance` (`ESSENTIAL`, `IMPORTANT`,
`DECORATIVE`), `confidence`, `sources` (quais providers a viram) e, quando há dúvida,
`needsReview` + `alternatives`.

Exemplo real (análise mock do vídeo sintético):

```json
{
  "id": "OBJECT_001",
  "type": "object",
  "label": "Copo de vidro",
  "attributes": {"class": "glass", "contents": "água", "material": "vidro"},
  "importance": "ESSENTIAL",
  "confidence": 0.858,
  "needsReview": true,
  "alternatives": [{"label": "Taça", "confidence": 0.708, "source": "mock-detector"}],
  "trackIds": ["TRACK_0013", "TRACK_0027"],
  "sources": ["mock-multimodal", "mock-detector", "mock-tracker"]
}
```

Entidades **derivadas** apontam para a origem: os fragmentos existem porque o copo quebrou.

```json
{"id": "OBJECT_005", "label": "Fragmentos de vidro", "derivedFrom": "OBJECT_001",
 "replaceable": false, "importance": "IMPORTANT"}
```

### Ações e relações

Ações usam um vocabulário fechado de verbos (`domain/vocabulary.py`), e cada verbo declara
de quais propriedades depende — é daí que sai a análise de impacto:

```json
{"id": "ACTION_002", "verb": "fall", "label": "O copo cai",
 "actorId": "OBJECT_001", "targetIds": ["FLOOR_001"],
 "startTime": 3.0, "endTime": 4.8, "shotIds": ["SHOT_002"],
 "essential": true, "physics": ["gravity", "motion"]}
```

Relações formam o grafo de cena (`holds`, `looks_at`, `in_front_of`, `on_top_of`,
`wears`…), sempre com intervalo de tempo e shots:

```json
{"id": "REL_003", "subjectId": "CHARACTER_001", "predicate": "looks_at",
 "objectId": "OBJECT_001", "startTime": 3.0, "endTime": 6.24,
 "shotIds": ["SHOT_002", "SHOT_003"]}
```

## Original e atual

- O **DNA original** é gravado uma vez, como JSON (JSONB no Postgres), e nunca muda. As
  mesmas informações são normalizadas em tabelas (`shots`, `entities`, `actions`…) para
  consultas e para o editor.
- O **DNA atual** não é gravado: é calculado como
  `apply_operations(original, operações ACTIVE em ordem de sequência)`.
- `GET /projects/{id}/video-dna?view=original|current` devolve um ou outro.

Assim, desfazer é só mudar o status de uma operação, versões são listas de operações e o
plano de geração pode congelar exatamente o que foi pedido.

## Operações de edição

| Operação | Exemplo | Observação |
|----------|---------|------------|
| `SET_ATTRIBUTE` | `HAIR_001.style = cacheado` | exige `property` |
| `CHANGE_APPEARANCE` | "camiseta com listras finas" | dict ou instrução livre |
| `REPLACE` | `OBJECT_001 → {"label": "Prato", "class": "plate"}` | exige `newValue.label`; reescreve entidades derivadas ("Fragmentos de prato") e resolve a dúvida da análise |
| `REMOVE` | remover a planta | entidade marcada `removed` |
| `KEEP` | "não mexer no sofá" | trava explícita |
| `APPLY_PRESET` | `ENVIRONMENT_001 → modern_apartment` | exige `newValue.presetId` |
| `ADD_ENTITY` | "garrafa de água ao lado do copo" | cria `OBJECT_1xx` com posição relativa |
| `CORRECT` | "não é copo, é taça" | corrige a análise; não gera nada |
| `INSTRUCTION` | instrução livre por elemento ou geral | |

`validate_operation` recusa o que não faz sentido para o elemento (ex.: `APPLY_PRESET`
num cabelo, editar algo marcado como não editável).

**Undo/redo:** undo marca a última operação ativa como `UNDONE`; redo reativa a mais antiga
desfeita; uma nova operação descarta (`DISCARDED`) o que estava desfeito — o comportamento
de qualquer editor.

## Impacto

Para cada operação, `domain/impact.py` calcula:

1. **Tipo de mudança** (`ChangeKind`) e nível base: cor/aparência local = baixo; objeto,
   parte do ambiente, aparência de personagem, instrução = médio; ambiente inteiro, troca
   ou remoção de personagem = alto. Correções de metadados = nenhum.
2. **Shots afetados**: aparições da entidade e de suas filhas (roupas de um personagem,
   partes de um ambiente).
3. **Dependências**, a partir das ações, relações e derivações do DNA:

| Dependência | Quando aparece | Exemplo (copo → prato) |
|-------------|----------------|------------------------|
| `HAND_INTERACTION` | ação de segurar/pegar/entregar | "A mão de Menino precisa segurar Prato" |
| `PHYSICS_MOTION` | ação com física (cair, rolar, voar) | "Prato precisa cair acompanhando o movimento original" |
| `DESTRUCTION_FX` | ação de quebrar/derramar | "Prato deve quebrar e os fragmentos devem parecer de prato" |
| `DERIVED_ENTITY` | entidade com `derivedFrom` | "Fragmentos de vidro → Fragmentos de prato" |
| `GAZE_TARGET` | relação `looks_at` | "Menino olha para Prato: o olhar deve continuar coerente" |
| `CONTACT_SURFACE` | contato com piso/mesa | "Contato entre Prato e Piso de madeira deve ser preservado" |
| `OCCLUSION` | elemento passa na frente/atrás de outro | |
| `CONTINUITY` | elemento em vários shots | "Prato deve permanecer igual em 6 shots" |
| `LIGHTING` | troca de ambiente ou de vista da janela | "A luz que entra pela janela deve combinar com a nova vista" |
| `STORY_ROLE` | elemento essencial | "Elemento essencial da história (papel OBJETO_A)" |
| `CHILD_ELEMENTS` | ambiente com partes | sala → apartamento leva parede, piso, janela |
| `AUDIO_SFX` | ação com som característico | marcada `futureFeature`: LOCK AUDIO mantém o áudio original |

4. **Nível final**: dependências de física, interação ou tracking elevam para alto.
5. **Avisos**:
   - `LOW_CONFIDENCE` — elemento incerto que a edição não resolveu (trocá-lo resolve);
   - `INCOMPATIBLE_ACTION` — o novo objeto não tem uma propriedade que a ação exige (trocar
     o copo por algo que não quebra, numa cena em que ele quebra); bloqueante quando LOCK
     STORY está ligado e a ação é essencial;
   - `PHYSICS_UNKNOWN` — classe nova fora do vocabulário: revisar o resultado;
   - `STORY_LOCK` / `STORY_CHANGE` — remover um elemento elimina uma ação essencial;
     bloqueante com LOCK STORY.

O mesmo relatório alimenta o card de impacto do editor (antes de aplicar), a lista de
alterações da tela de revisão e o planejador.

## Caso de teste da especificação (§79)

História: um menino segura um copo de vidro na sala; o copo cai e quebra; a mãe entra,
vê o copo quebrado e repreende o menino. Alterações: camiseta azul, cabelo cacheado,
copo → prato, sala → apartamento moderno, vista da janela → praia.

O que o sistema reconhece (coberto por `test_flow_generation.py::test_spec79_generation_plan_recognizes_dependencies`):

- camiseta e cabelo: impacto baixo, continuidade do personagem em todos os shots dele
  (Character Reference Pack);
- copo → prato: impacto alto — mão, queda, quebra, fragmentos derivados, olhar do menino,
  contato com o piso, papel essencial na história, efeito sonoro (futuro);
- sala → apartamento: impacto alto — partes do ambiente, iluminação, Scene Reference Pack;
- vista da janela: iluminação coerente com a nova vista;
- o plano escolhe reconstrução de shot onde as alterações se acumulam e o QA verifica o
  prato durante a queda.
