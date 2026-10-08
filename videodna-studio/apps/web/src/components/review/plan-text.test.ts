import { describe, expect, it } from "vitest";

import {
  type PlanShot,
  type PlanWarning,
  continuityText,
  durationLabel,
  groupWarnings,
  keptText,
  parseEdit,
  plainText,
  sceneName,
  scenesLabel,
  summarizeChanges,
} from "./plan-text";

const edit = (description: string, entityLabel = "Elemento") => ({
  operationId: description,
  entityLabel,
  changeKind: "OBJECT_REPLACE",
  description,
});

const shot = (n: number, descriptions: string[]): PlanShot => ({
  shotKey: `SHOT_00${n}`,
  index: n - 1,
  startTime: n - 1,
  endTime: n,
  strategy: "SHOT_RECONSTRUCTION",
  estimatedCost: 1,
  edits: descriptions.map((d) => edit(d)),
  steps: [],
  dependencies: [],
  referencePacks: [],
});

const warn = (code: string, message: string, blocking = false, entityKey: string | null = null): PlanWarning => ({
  code,
  message,
  blocking,
  entityKey,
});

describe("scene names and server text", () => {
  it("names scenes from the index or the key, never SHOT_00N", () => {
    expect(sceneName("SHOT_003", 2)).toBe("Cena 3");
    expect(sceneName("SHOT_012")).toBe("Cena 12");
    expect(plainText("SHOT_003: nenhum provider disponível para SHOT_RECONSTRUCTION.")).toBe(
      "Cena 3: nenhum serviço de IA disponível para “cena refeita por inteiro”.",
    );
    expect(plainText("LOCK AUDIO ativo: o áudio de cada shot")).toBe("“Manter o som” está ligado: o áudio de cada cena");
  });
});

describe("what will change", () => {
  it("splits before → after and keeps the user's instruction apart", () => {
    expect(parseEdit(edit("Copo de vidro → Prato"))).toEqual({ before: "Copo de vidro", after: "Prato", note: null });
    expect(
      parseEdit(edit("Vista da janela: rua residencial → Vista da janela: praia (Quero que pela janela apareça uma praia.)")),
    ).toEqual({
      before: "Vista da janela: rua residencial",
      after: "Vista da janela: praia",
      note: "Quero que pela janela apareça uma praia.",
    });
    // A one-word parenthesis is part of the label, not an instruction.
    expect(parseEdit(edit("Copo → Copo (vidro)")).after).toBe("Copo (vidro)");
    expect(parseEdit(edit("Camiseta vermelha: alterar aparência"))).toEqual({
      before: "Camiseta vermelha",
      after: "nova aparência",
      note: null,
    });
    expect(parseEdit(edit("Remover Copo de vidro"))).toEqual({ before: null, after: "Remover Copo de vidro", note: null });
    expect(parseEdit(edit("Instrução: deixe mais claro")).after).toBe("Pedido: “deixe mais claro”");
    expect(parseEdit(edit("Pedido: deixe mais claro")).after).toBe("Pedido: “deixe mais claro”");
    expect(parseEdit(edit("REPLACE", "Copo")).after).toBe("Substituir Copo");
  });

  it("lists each change once with the scenes it touches", () => {
    const changes = summarizeChanges([
      shot(1, ["Copo de vidro → Prato", "Sala de estar → Apartamento moderno"]),
      shot(2, ["Sala de estar → Apartamento moderno"]),
      shot(3, []),
    ]);
    expect(changes.map((c) => [c.after, c.scenes.length])).toEqual([
      ["Prato", 1],
      ["Apartamento moderno", 2],
    ]);
    expect(scenesLabel(1, 3)).toBe("em 1 cena");
    expect(scenesLabel(2, 3)).toBe("em 2 cenas");
    expect(scenesLabel(3, 3)).toBe("em todas as cenas");
  });

  it("says what stays the same, how long it takes and how continuity is kept", () => {
    expect(keptText(undefined)).toBe(
      "Fica como no original: a história, a câmera, os movimentos, o som e a duração das cenas.",
    );
    expect(keptText({ story: true, camera: false, motion: false, audio: true, timing: false })).toBe(
      "Fica como no original: a história e o som.",
    );
    expect(keptText({ story: false, camera: false, motion: false, audio: false, timing: false })).toBeNull();
    expect(durationLabel(45)).toBe("menos de 1 min");
    expect(durationLabel(120)).toBe("cerca de 2 min");
    const pack = (label: string, description: string) => ({ id: label, kind: "character", entityKey: "X", label, description, shotKeys: [] });
    expect(
      continuityText([
        pack("Character Reference Pack — Menino", "Menino: Cabelo cacheado, Camiseta azul"),
        pack("Referência do cenário: Apartamento moderno", "Apartamento moderno: Parede, Piso"),
      ]),
    ).toBe("Para não mudar de uma cena para outra, a IA usa sempre o mesmo visual de Menino e Apartamento moderno.");
    expect(continuityText([])).toBeNull();
  });
});

describe("warnings", () => {
  it("turns three story-lock warnings about one element into one blocking notice with a fix", () => {
    const g = groupWarnings([
      warn("STORY_LOCK", "Remover Copo de vidro elimina a ação essencial 'Menino segura o copo'.", true, "OBJECT_001"),
      warn("STORY_LOCK", "Remover Copo de vidro elimina a ação essencial 'O copo cai'.", true, "OBJECT_001"),
      warn("STORY_LOCK", "Remover Copo de vidro elimina a ação essencial 'O copo quebra'.", true, "OBJECT_001"),
      warn("LOW_CONFIDENCE", "Não tenho certeza sobre este elemento (Copo de vidro / Taça). Confirme antes de gerar.", false, "OBJECT_001"),
      warn("AUDIO_LOCKED", "LOCK AUDIO ativo: o áudio original será mantido, inclusive efeitos sonoros."),
      warn("TIMING_LOCKED", "LOCK TIMING ativo: duração e ritmo de cada shot serão preservados."),
    ]);
    expect(g.lockConflict).toBe(true);
    expect(g.blocking).toHaveLength(1);
    expect(g.blocking[0]).toMatchObject({
      title: "Esta mudança quebra a história do vídeo",
      text: "Remover Copo de vidro tira da história os momentos “Menino segura o copo”, “O copo cai” e “O copo quebra”.",
      action: "editor",
      entityKey: "OBJECT_001",
    });
    expect(g.blocking[0].fix).toContain("Manter a história");
    expect(g.notes.map((n) => n.text)).toEqual([
      "O som original fica igual, inclusive os efeitos sonoros — eles podem não combinar com o que você mudou.",
      "A IA ficou em dúvida: é Copo de vidro ou Taça?",
    ]);
    const shown = [...g.blocking, ...g.notes].flatMap((n) => [n.title, n.text, n.fix, n.actionLabel]).join(" ");
    expect(shown).not.toMatch(/LOCK|SHOT_|OBJECT_|provider/);
  });

  it("reads the planner's plainer wording too, without repeating its advice", () => {
    const advice = "Para remover mesmo assim, desligue “Manter a história” em Opções avançadas.";
    const g = groupWarnings([
      warn("STORY_LOCK", `Remover Copo de vidro apaga uma parte importante da história (“O copo cai”). ${advice}`, true, "O1"),
      warn("STORY_LOCK", `Remover Copo de vidro apaga uma parte importante da história (“O copo quebra”). ${advice}`, true, "O1"),
      warn(
        "INCOMPATIBLE_ACTION",
        "Prato talvez não caiba na mão como no vídeo original. Escolha outro objeto ou desligue “Manter a história” em Opções avançadas.",
        true,
        "O2",
      ),
      warn("LOW_CONFIDENCE", "A análise não tem certeza do que é este elemento (Copo de vidro ou Taça). Confirme o que é antes de gerar.", false, "O1"),
    ]);
    expect(g.blocking.map((n) => n.text)).toEqual([
      "Remover Copo de vidro tira da história os momentos “O copo cai” e “O copo quebra”.",
      "Prato talvez não caiba na mão como no vídeo original.",
    ]);
    expect(g.blocking.every((n) => n.fix?.includes("Manter a história"))).toBe(true);
    expect(g.notes[0].text).toBe("A IA ficou em dúvida: é Copo de vidro ou Taça?");
  });

  it("falls back to the server's sentences, each once, when a message has another shape", () => {
    const g = groupWarnings([
      warn("STORY_LOCK", "O copo some da cena (“A”). Desligue “Manter a história”.", true, "O1"),
      warn("STORY_LOCK", "O copo some da cena (“B”). Desligue “Manter a história”.", true, "O1"),
    ]);
    expect(g.blocking[0].text).toBe("O copo some da cena (“A”). Desligue “Manter a história”. O copo some da cena (“B”).");
    expect(g.blocking[0].fix).toBeUndefined();
  });

  it("explains missing services and budget with what to change on this page", () => {
    const g = groupWarnings([
      warn("NO_PROVIDER", "SHOT_002: nenhum provider disponível para LOCALIZED_EDIT.", true),
      warn("NO_PROVIDER", "SHOT_005: nenhum provider disponível para LOCALIZED_EDIT.", true),
      warn("INSUFFICIENT_CREDITS", "Orçamento insuficiente: gasto 1.00 + estimativa 9.00 > limite 5.00 BRL.", true),
      warn("STRATEGY_ESCALATED", "SHOT_003: nenhum provider para LOCALIZED_EDIT; usando SHOT_RECONSTRUCTION."),
      warn("NO_AI_QA", "Sem inspetor de IA disponível; apenas QA técnico será executado."),
    ]);
    expect(g.lockConflict).toBe(false);
    expect(g.blocking.map((n) => [n.text, n.action])).toEqual([
      ["O custo desta geração, somado ao que você já gastou, passa do limite da sua conta.", "options"],
      ["Nenhum serviço de IA disponível consegue fazer a mudança nas cenas 2 e 5.", "options"],
    ]);
    expect(g.technical).toEqual([
      "Cena 3: o jeito mais simples de editar não está disponível; será usado “cena refeita por inteiro”.",
    ]);
    expect(g.notes.map((n) => n.text)).toEqual([
      "A conferência automática por IA não está disponível; o resultado passa só pela checagem técnica. Assista ao resultado com atenção.",
    ]);
  });

  it("keeps the server's sentence when it is already plain, including codes this screen does not know", () => {
    const segmentation = "Cena 2: a IA não vai recortar o contorno exato do elemento; a mudança pode ficar menos precisa nas bordas.";
    const audioOff = "“Manter o som” está desligado: o vídeo gerado vai ficar sem som.";
    const g = groupWarnings([warn("NO_SEGMENTATION", segmentation), warn("AUDIO_OFF", audioOff)]);
    expect(g.technical).toEqual([segmentation]);
    expect(g.notes.map((n) => n.text)).toEqual([audioOff]);
  });

  it("flags a plan with nothing to generate", () => {
    expect(groupWarnings([warn("NOTHING_TO_GENERATE", "Nenhuma alteração visual para gerar.", true)]).nothing).toBe("no-visual");
    expect(groupWarnings([warn("NO_SHOTS_AFFECTED", "As alterações não afetam nenhum shot visível.", true)]).nothing).toBe(
      "no-scenes",
    );
    expect(groupWarnings([]).nothing).toBeNull();
  });
});
