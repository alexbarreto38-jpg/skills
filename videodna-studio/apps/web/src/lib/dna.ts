import type { DnaEntity, EntityTrack, Shot, VideoDNA } from "@videodna/api-client";

export interface TreeNode {
  key: string;
  entity: DnaEntity;
  children: TreeNode[];
}

export interface DnaTree {
  characters: TreeNode[];
  scenery: TreeNode[];
  objects: TreeNode[];
}

function childrenOf(dna: VideoDNA, key: string, skipTypes: Set<string> = new Set()): TreeNode[] {
  return dna.entities
    .filter((e) => e.parentId === key && !skipTypes.has(e.type))
    .map((e) => ({ key: e.id, entity: e, children: childrenOf(dna, e.id, skipTypes) }));
}

const WARDROBE_ORDER = ["upper", "lower", "footwear", "full"];

/** Tree shown in the left panel: Personagens / Cenário / Objetos (spec §36). */
export function buildTree(dna: VideoDNA): DnaTree {
  const characters = dna.entities
    .filter((e) => e.type === "character")
    .map((e) => {
      const children = childrenOf(dna, e.id).sort((a, b) => {
        const rank = (n: TreeNode) =>
          n.entity.type === "hair"
            ? 0
            : n.entity.type === "wardrobe"
              ? 1 + WARDROBE_ORDER.indexOf(n.entity.subtype ?? "upper")
              : 9;
        return rank(a) - rank(b);
      });
      return { key: e.id, entity: e, children };
    });
  const scenery = dna.entities
    .filter((e) => e.type === "environment")
    .map((e) => ({ key: e.id, entity: e, children: childrenOf(dna, e.id, new Set(["object"])) }));
  const objects = dna.entities
    .filter((e) => e.type === "object")
    .map((e) => ({ key: e.id, entity: e, children: [] }));
  return { characters, scenery, objects };
}

export function entityMap(dna: VideoDNA | undefined): Map<string, DnaEntity> {
  return new Map((dna?.entities ?? []).map((e) => [e.id, e]));
}

/** Shots an entity is visible in (falls back to its parent / scene). */
export function shotsForEntity(dna: VideoDNA, key: string): string[] {
  const entity = dna.entities.find((e) => e.id === key);
  if (!entity) return [];
  const own = (entity.appearances ?? []).map((a) => a.shotId);
  if (own.length) return own;
  if (entity.type === "environment") {
    return dna.scenes.filter((s) => s.environmentId === key).flatMap((s) => s.shotIds);
  }
  return entity.parentId ? shotsForEntity(dna, entity.parentId) : [];
}

export function isModified(entity: DnaEntity | undefined): boolean {
  return !!entity?.edit && (entity.edit.modified || entity.edit.removed || entity.edit.added);
}

/** Shots touched by any edit in the current DNA (timeline markers). */
export function modifiedShots(dna: VideoDNA | undefined): Set<string> {
  const out = new Set<string>();
  if (!dna) return out;
  for (const entity of dna.entities) {
    if (isModified(entity)) shotsForEntity(dna, entity.id).forEach((s) => out.add(s));
  }
  return out;
}

export function shotAt(dna: VideoDNA | undefined, time: number): Shot | undefined {
  return dna?.shots.find((s) => time >= s.startTime && time < s.endTime) ?? dna?.shots.at(-1);
}

export interface VisibleBox {
  entityKey: string;
  x: number;
  y: number;
  w: number;
  h: number;
  occluded: boolean;
}

function boxAt(track: EntityTrack, time: number): VisibleBox | null {
  const samples = track.samples ?? [];
  if (!samples.length || time < track.startTime - 0.05 || time > track.endTime + 0.05) return null;
  let a = samples[0];
  let b = samples[samples.length - 1];
  for (let i = 0; i < samples.length - 1; i += 1) {
    if (samples[i].time <= time && samples[i + 1].time >= time) {
      a = samples[i];
      b = samples[i + 1];
      break;
    }
  }
  const span = b.time - a.time;
  const k = span > 0 ? Math.min(1, Math.max(0, (time - a.time) / span)) : 0;
  const lerp = (p: number, q: number) => p + (q - p) * k;
  return {
    entityKey: track.entityId,
    x: lerp(a.bbox.x, b.bbox.x),
    y: lerp(a.bbox.y, b.bbox.y),
    w: lerp(a.bbox.w, b.bbox.w),
    h: lerp(a.bbox.h, b.bbox.h),
    occluded: !!a.occluded,
  };
}

const SCENERY = new Set(["environment", "environment_part", "lighting"]);

/** Bounding boxes of tracked elements at a given time (player overlay).
 * Scenery (walls, floor...) covers most of the frame, so it is only drawn
 * when selected — otherwise it would swallow every click. */
export function visibleBoxes(dna: VideoDNA | undefined, time: number, selectedKey?: string | null): VisibleBox[] {
  if (!dna) return [];
  const types = new Map(dna.entities.map((e) => [e.id, e.type]));
  const out: VisibleBox[] = [];
  for (const track of dna.tracks ?? []) {
    if (SCENERY.has(types.get(track.entityId) ?? "") && track.entityId !== selectedKey) continue;
    const box = boxAt(track, time);
    if (box) out.push(box);
  }
  // Big boxes first so small ones (hair, cup) stay clickable on top.
  return out.sort((p, q) => q.w * q.h - p.w * p.h);
}

export function confidenceTone(confidence: number, threshold: number): "ok" | "warn" | "bad" {
  if (confidence < threshold) return "bad";
  if (confidence < Math.min(0.85, threshold + 0.2)) return "warn";
  return "ok";
}
