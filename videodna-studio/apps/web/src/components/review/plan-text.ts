import { OP_LABEL, label } from "@/lib/labels";

/**
 * Plain pt-BR wording for the review screen, derived from the generation plan
 * document. The plan speaks in shot keys, strategy enums and provider names;
 * the owner reads "Cena 3", "cena refeita por inteiro" and "a IA".
 *
 * Warnings are rewritten by `code` and only parsed for the names they carry
 * (labels, story moments, scenes). When a message does not have the expected
 * shape, the sanitised original is shown instead, so a server-side rewording
 * degrades to the server's text rather than to nothing.
 */

// --- the parts of the plan document (GenerationPlanSpec as camelCase JSON) this screen reads ----

export interface PlanEdit {
  operationId: string;
  entityKey?: string | null;
  entityLabel: string;
  changeKind: string;
  description: string;
}
export interface PlanStep {
  strategy: string;
  provider: string;
  model?: string | null;
  estimatedCost: number;
  chunks: number;
}
export interface PlanDependency {
  type: string;
  description: string;
  futureFeature?: boolean;
}
export interface PlanShot {
  shotKey: string;
  index: number;
  startTime: number;
  endTime: number;
  strategy: string;
  estimatedCost: number;
  qaProvider?: string | null;
  edits: PlanEdit[];
  steps: PlanStep[];
  dependencies: PlanDependency[];
  referencePacks: string[];
}
export interface PlanPack {
  id: string;
  kind: string;
  entityKey: string;
  label: string;
  description: string;
  shotKeys: string[];
}
export interface PlanWarning {
  code: string;
  message: string;
  blocking: boolean;
  entityKey?: string | null;
}
export type LockKey = "story" | "camera" | "motion" | "audio" | "timing";
export interface PlanDoc {
  summary: { totalShots: number; affectedShots: number; passthroughShots: number; generations: number; editCount: number };
  shots: PlanShot[];
  referencePacks: PlanPack[];
  warnings: PlanWarning[];
  locks?: Partial<Record<LockKey, boolean>>;
  estimatedCost: number;
  estimatedCostWithRepairs: number;
  currency: string;
  resolutionLabel: string;
  maxRetries: number;
  providers: string[];
  expectedDurationSec: number;
}

// --- small wording helpers --------------------------------------------------------------------

/** ["a"] -> "a"; ["a", "b", "c"] -> "a, b e c". */
export function listPt(items: string[], last = "e"): string {
  if (items.length <= 1) return items.join("");
  return `${items.slice(0, -1).join(", ")} ${last} ${items[items.length - 1]}`;
}

export function plural(n: number, singular: string, pluralForm: string): string {
  return `${n} ${n === 1 ? singular : pluralForm}`;
}

const quoted = (s: string) => `“${s}”`;
const unique = <T,>(items: T[]) => [...new Set(items)];

/** "SHOT_003" (or index 2) -> "Cena 3". */
export function sceneName(shotKey: string, index?: number | null): string {
  if (index != null) return `Cena ${index + 1}`;
  const digits = /(\d+)$/.exec(shotKey)?.[1];
  return digits ? `Cena ${Number(digits)}` : "Uma cena";
}

/** How each scene will be made, in words (shown only inside the technical details). */
export const STRATEGY_PLAIN: Record<string, string> = {
  PASSTHROUGH: "Fica igual ao original",
  ATTRIBUTE_EDIT: "Ajuste de cor ou detalhe",
  LOCALIZED_EDIT: "Mudança só no elemento",
  BACKGROUND_REPLACEMENT: "Troca do cenário",
  SHOT_RECONSTRUCTION: "Cena refeita por inteiro",
  FULL_REGENERATION: "Cena criada do zero",
};

/** What the AI has to be careful about in a scene (technical details only). */
export const DEPENDENCY_PLAIN: Record<string, string> = {
  HAND_INTERACTION: "Alguém segura ou toca",
  PHYSICS_MOTION: "Algo cai ou se move",
  DESTRUCTION_FX: "Algo quebra",
  CONTACT_SURFACE: "Encosta em uma superfície",
  GAZE_TARGET: "Alguém olha para ele",
  OCCLUSION: "Fica atrás de outra coisa",
  CONTINUITY: "Aparece em outras cenas",
  DERIVED_ENTITY: "Gera outros elementos (ex.: cacos)",
  LIGHTING: "Luz e sombra",
  STORY_ROLE: "Importante na história",
  AUDIO_SFX: "Tem som próprio",
  CHILD_ELEMENTS: "Inclui partes do cenário",
};

const LOCK_NAME: Record<string, string> = {
  STORY: "Manter a história",
  CAMERA: "Manter a câmera",
  MOTION: "Manter os movimentos",
  AUDIO: "Manter o som",
  TIMING: "Manter o tempo",
};

/** Last line of defence for server text: no shot keys, strategy enums, "provider" or "shot". */
export function plainText(text: string): string {
  return text
    .replace(/\b(PASSTHROUGH|ATTRIBUTE_EDIT|LOCALIZED_EDIT|BACKGROUND_REPLACEMENT|SHOT_RECONSTRUCTION|FULL_REGENERATION)\b/g, (k) =>
      quoted(STRATEGY_PLAIN[k].toLowerCase()),
    )
    .replace(/\bSHOT_0*(\d+)\b/g, "Cena $1")
    .replace(/\bLOCK (STORY|CAMERA|MOTION|AUDIO|TIMING) ativo\b/g, (_, k: string) => `${quoted(LOCK_NAME[k])} está ligado`)
    .replace(/\bproviders\b/gi, "serviços de IA")
    .replace(/\bprovider\b/gi, "serviço de IA")
    .replace(/\bshots\b/gi, "cenas")
    .replace(/\bshot\b/gi, "cena");
}

/** Scene numbers named in a message, whether the server wrote "SHOT_003" or "Cena 3". */
function scenesIn(text: string): number[] {
  return [...text.matchAll(/\bSHOT_0*(\d+)\b|\bCena (\d+)\b/g)].map((m) => Number(m[1] ?? m[2]));
}

function scenesPhrase(numbers: number[]): string {
  const n = unique(numbers).sort((a, b) => a - b);
  if (n.length === 0) return "que você pediu";
  if (n.length === 1) return `na Cena ${n[0]}`;
  return `nas cenas ${listPt(n.map(String))}`;
}

// --- "O que vai mudar" ---------------------------------------------------------------------------

export interface Change {
  key: string;
  /** What it is now, or null when the change has no "before" (remove, add, free instruction). */
  before: string | null;
  after: string;
  /** The user's own words, when they typed an instruction. */
  note: string | null;
  scenes: string[];
}

/** One planned edit as "before → after", from the planner's description. */
export function parseEdit(edit: Pick<PlanEdit, "description" | "entityLabel">): Omit<Change, "key" | "scenes"> {
  let text = edit.description.trim();
  if (/^[A-Z_]+$/.test(text)) return { before: null, after: `${label(OP_LABEL, text)} ${edit.entityLabel}`.trim(), note: null };
  const instruction = /^(?:Instrução|Pedido):\s*(.+)$/s.exec(text);
  if (instruction) return { before: null, after: `Pedido: ${quoted(instruction[1].trim())}`, note: null };
  let note: string | null = null;
  // The planner appends the user's instruction as " (…)". Only a parenthesis
  // holding a phrase (with a space) is taken as one, so "Copo (vidro)" stays a label.
  const tail = /^(.*\S)\s+\(([^()]*\s[^()]*)\)$/s.exec(text);
  if (tail) {
    text = tail[1];
    note = tail[2].trim();
  }
  const appearance = /^(.+?):\s*alterar aparência$/i.exec(text);
  if (appearance) return { before: appearance[1], after: "nova aparência", note };
  const arrow = text.indexOf(" → ");
  if (arrow > 0) return { before: text.slice(0, arrow), after: text.slice(arrow + 3), note };
  return { before: null, after: text, note };
}

/** Every distinct change in the plan, once, with the scenes it touches. */
export function summarizeChanges(shots: PlanShot[]): Change[] {
  const byKey = new Map<string, Change>();
  for (const shot of shots) {
    for (const edit of shot.edits) {
      const key = edit.description;
      let change = byKey.get(key);
      if (!change) {
        change = { key, ...parseEdit(edit), scenes: [] };
        byKey.set(key, change);
      }
      if (!change.scenes.includes(shot.shotKey)) change.scenes.push(shot.shotKey);
    }
  }
  return [...byKey.values()];
}

export function scenesLabel(count: number, total: number): string {
  if (total > 1 && count === total) return "em todas as cenas";
  return `em ${plural(count, "cena", "cenas")}`;
}

/** 120 -> "cerca de 2 min"; 45 -> "menos de 1 min". */
export function durationLabel(seconds: number): string {
  if (seconds < 60) return "menos de 1 min";
  return `cerca de ${Math.round(seconds / 60)} min`;
}

const KEPT: { key: LockKey; text: string }[] = [
  { key: "story", text: "a história" },
  { key: "camera", text: "a câmera" },
  { key: "motion", text: "os movimentos" },
  { key: "audio", text: "o som" },
  { key: "timing", text: "a duração das cenas" },
];

/** What the plan keeps as in the original (the editor's "O que manter igual ao original"). */
export function keptText(locks: PlanDoc["locks"]): string | null {
  const kept = KEPT.filter((k) => locks?.[k.key] ?? true).map((k) => k.text);
  return kept.length ? `Fica como no original: ${listPt(kept)}.` : null;
}

function packName(pack: PlanPack): string {
  return / — (.+)$/.exec(pack.label)?.[1] ?? pack.description.split(": ")[0] ?? pack.label;
}

/** Reference packs, as the one sentence a non-technical reader needs. */
export function continuityText(packs: PlanPack[]): string | null {
  const names = unique(packs.map(packName).filter(Boolean));
  if (!names.length) return null;
  return `Para não mudar de uma cena para outra, a IA usa sempre o mesmo visual de ${listPt(names)}.`;
}

// --- warnings ------------------------------------------------------------------------------------

export interface Notice {
  id: string;
  title?: string;
  text: string;
  /** What to do about it. */
  fix?: string;
  /** "editor": a button that opens the editor on `entityKey`; "options": fixed with the choices on this page. */
  action: "editor" | "options" | null;
  actionLabel?: string;
  entityKey: string | null;
}

export interface WarningGroups {
  /** Stop generation; shown at the top with a way to fix each one. */
  blocking: Notice[];
  /** Worth knowing before generating. */
  notes: Notice[];
  /** How the plan adapted (fallbacks); only inside the technical details. */
  technical: string[];
  /** The plan has nothing to generate: the page shows a way back instead of a plan. */
  nothing: "no-visual" | "no-scenes" | null;
  /** A blocking conflict with "Manter a história" (the steps bar then says to go back and adjust). */
  lockConflict: boolean;
}

// How the plan adapted per scene; only inside the technical details.
const TECHNICAL = new Set(["STRATEGY_ESCALATED", "NO_SEGMENTATION"]);
// Shown as "Fica como no original: …" from the plan's locks instead.
const COVERED = new Set(["TIMING_LOCKED"]);
const STORY_FIX =
  "Desfaça essa mudança no editor ou, se quiser mesmo mudar a história, desligue “Manter a história” em Opções avançadas.";

/** True when server text has no shot keys, enum values, "provider", "QA" or "LOCK" left in it. */
const isPlain = (text: string) => !/SHOT_\d|\b[A-Z]{2,}_[A-Z_]+\b|provider|\bQA\b|\bLOCK\b/.test(text);

/** The server's sentence when it is already plain; otherwise this screen's own words for the code. */
function codeText(w: PlanWarning): string {
  if (isPlain(w.message)) return w.message;
  const scene = scenesIn(w.message)[0];
  const where = scene ? `Cena ${scene}: ` : "";
  if (w.code === "STRATEGY_ESCALATED") {
    const used = /usando (\w+)/.exec(w.message)?.[1];
    if (used && STRATEGY_PLAIN[used])
      return `${where}o jeito mais simples de editar não está disponível; será usado ${quoted(STRATEGY_PLAIN[used].toLowerCase())}.`;
  }
  if (w.code === "NO_SEGMENTATION")
    return `${where}a IA não vai recortar o contorno exato do elemento; a mudança pode ficar menos precisa nas bordas.`;
  if (w.code === "NO_AI_QA")
    return "A conferência automática por IA não está disponível; o resultado passa só pela checagem técnica. Assista ao resultado com atenção.";
  return plainText(w.message);
}

/** Captures `pattern` from every message, or null when any message has another shape. */
function captureAll(ws: PlanWarning[], pattern: RegExp): RegExpExecArray[] | null {
  const found = ws.map((w) => pattern.exec(w.message));
  return found.every((m): m is RegExpExecArray => m !== null) ? found : null;
}

/** The sanitised server messages, each sentence once (one warning per story moment repeats the advice). */
function fallback(ws: PlanWarning[]): string {
  const sentences = ws.flatMap((w) => plainText(w.message).split(/(?<=[.!?])\s+/));
  return unique(sentences.map((x) => x.trim()).filter(Boolean)).join(" ");
}

/** True when the server's own text already says what to do, so the screen does not say it twice. */
const hasAdvice = (text: string) => /Manter a história|Confira|Confirme|Escolha outr/i.test(text);

// A removal that erases a story moment, in the planner's older and newer wording.
const STORY_MOMENT = /^Remover (.+?) (?:elimina a ação essencial '(.+?)'|apaga uma parte importante da história \(“(.+?)”\))/;

function entityNotice(code: string, ws: PlanWarning[], blocking: boolean, entityKey: string | null): Notice {
  const id = `${code}:${entityKey ?? ""}:${blocking ? "b" : "n"}`;
  const base = { id, entityKey, action: entityKey ? ("editor" as const) : null };
  switch (code) {
    case "STORY_LOCK":
    case "STORY_CHANGE": {
      const m = captureAll(ws, STORY_MOMENT);
      const moments = m ? unique(m.map((x) => x[2] ?? x[3])) : [];
      const text = m
        ? `Remover ${m[0][1]} tira da história ${moments.length === 1 ? "o momento" : "os momentos"} ${listPt(moments.map(quoted))}.`
        : fallback(ws);
      if (!blocking) return { ...base, action: null, text: m ? `${text} A história do vídeo vai mudar.` : text };
      return {
        ...base,
        title: "Esta mudança quebra a história do vídeo",
        text,
        fix: hasAdvice(text) ? undefined : STORY_FIX,
        actionLabel: "Corrigir no editor",
      };
    }
    case "INCOMPATIBLE_ACTION": {
      const old = captureAll(ws, /^(.+?) pode não ser compatível com a ação '(.+?)'/);
      const plain = old ? null : captureAll(ws, /^(.+? como no vídeo original\.)/);
      const text = old
        ? `${old[0][1]} talvez não consiga ${listPt(unique(old.map((x) => quoted(x[2]))))} como no vídeo original.`
        : plain
          ? unique(plain.map((x) => plainText(x[1]))).join(" ")
          : fallback(ws).replace(/\s*\([^()]*\)\.$/, ".");
      if (!blocking)
        return { ...base, action: null, text: hasAdvice(text) ? text : `${text} Confira essa parte no resultado.` };
      return {
        ...base,
        title: "Esta troca pode não funcionar na história",
        text,
        fix: hasAdvice(text)
          ? undefined
          : "Escolha outra opção para este item no editor ou desligue “Manter a história” em Opções avançadas.",
        actionLabel: "Corrigir no editor",
      };
    }
    case "PHYSICS_UNKNOWN": {
      const m = captureAll(ws, /^Não sei se (.+?) consegue '(.+?)'/);
      const text = m
        ? `A IA não sabe se ${m[0][1]} consegue ${listPt(unique(m.map((x) => quoted(x[2]))))}. Confira essa parte no resultado.`
        : fallback(ws);
      return { ...base, action: null, text };
    }
    case "LOW_CONFIDENCE": {
      // "(Copo de vidro / Taça)" or "(Copo de vidro ou Taça)".
      const alternatives = /\(([^()]+)\)/.exec(ws[0].message)?.[1]?.split(" / ").map((x) => x.trim());
      return {
        ...base,
        text: alternatives?.length ? `A IA ficou em dúvida: é ${listPt(alternatives, "ou")}?` : fallback(ws),
        fix: "Confirme no editor para a mudança sair no item certo.",
        actionLabel: "Confirmar no editor",
      };
    }
    default:
      return blocking
        ? { ...base, title: "Algo impede a geração", text: fallback(ws), action: "editor", actionLabel: "Voltar ao editor" }
        : { ...base, action: null, text: fallback(ws) };
  }
}

export function groupWarnings(warnings: PlanWarning[]): WarningGroups {
  const out: WarningGroups = { blocking: [], notes: [], technical: [], nothing: null, lockConflict: false };
  // Several warnings about the same element (one per story moment) read as one.
  const grouped = new Map<string, { code: string; blocking: boolean; entityKey: string | null; items: PlanWarning[] }>();
  const noProvider: PlanWarning[] = [];

  for (const w of warnings) {
    if (w.code === "NOTHING_TO_GENERATE") out.nothing = "no-visual";
    else if (w.code === "NO_SHOTS_AFFECTED") out.nothing ??= "no-scenes";
    else if (COVERED.has(w.code)) continue;
    else if (TECHNICAL.has(w.code) && !w.blocking) out.technical.push(codeText(w));
    else if (w.code === "NO_AI_QA") out.notes.push({ id: w.code, text: codeText(w), action: null, entityKey: null });
    else if (w.code === "NO_PROVIDER") noProvider.push(w);
    else if (w.code === "AUDIO_LOCKED")
      out.notes.push({
        id: w.code,
        text: "O som original fica igual, inclusive os efeitos sonoros — eles podem não combinar com o que você mudou.",
        action: null,
        entityKey: null,
      });
    else if (w.code === "INSUFFICIENT_CREDITS")
      out.blocking.push({
        id: w.code,
        title: "Passa do seu limite de gastos",
        text: "O custo desta geração, somado ao que você já gastou, passa do limite da sua conta.",
        fix: "Escolha “Econômico” ou faça menos mudanças.",
        action: "options",
        entityKey: null,
      });
    else {
      const key = `${w.code}:${w.entityKey ?? ""}:${w.blocking}`;
      const group = grouped.get(key) ?? { code: w.code, blocking: w.blocking, entityKey: w.entityKey ?? null, items: [] };
      group.items.push(w);
      grouped.set(key, group);
    }
  }

  if (noProvider.length)
    out.blocking.push({
      id: "NO_PROVIDER",
      title: "Não dá para gerar com estas opções",
      text: `Nenhum serviço de IA disponível consegue fazer a mudança ${scenesPhrase(noProvider.flatMap((w) => scenesIn(w.message)))}.`,
      fix: "Escolha outra opção em “Qualidade” ou “Tipo de vídeo”.",
      action: "options",
      entityKey: null,
    });
  for (const g of grouped.values()) {
    const notice = entityNotice(g.code, g.items, g.blocking, g.entityKey);
    (g.blocking ? out.blocking : out.notes).push(notice);
    if (g.blocking && (g.code === "STORY_LOCK" || g.code === "INCOMPATIBLE_ACTION")) out.lockConflict = true;
  }
  out.notes = out.notes.filter((n, i, all) => all.findIndex((o) => o.text === n.text) === i);
  out.technical = unique(out.technical);
  return out;
}
