import type { VideoDNA } from "@videodna/api-client";
import { parseSseBlock } from "@videodna/api-client";
import { describe, expect, it } from "vitest";

import { buildTree, modifiedShots, shotsForEntity, visibleBoxes } from "./dna";
import { formatBytes, formatMoney, formatTime } from "./format";

const dna = {
  technical: { durationSec: 6, width: 1280, height: 720, fps: 25 },
  shots: [
    { id: "SHOT_001", index: 0, startTime: 0, endTime: 3 },
    { id: "SHOT_002", index: 1, startTime: 3, endTime: 6 },
  ],
  scenes: [{ id: "SCENE_001", shotIds: ["SHOT_001", "SHOT_002"], environmentId: "ENV" }],
  entities: [
    { id: "ENV", type: "environment", label: "Sala", appearances: [] },
    { id: "WALL", type: "environment_part", subtype: "wall", parentId: "ENV", label: "Parede" },
    { id: "BOY", type: "character", label: "Menino", appearances: [{ shotId: "SHOT_001", startTime: 0, endTime: 3 }] },
    { id: "SHIRT", type: "wardrobe", subtype: "upper", parentId: "BOY", label: "Camiseta", edit: { modified: true } },
    { id: "HAIR", type: "hair", parentId: "BOY", label: "Cabelo" },
    { id: "CUP", type: "object", label: "Copo", appearances: [{ shotId: "SHOT_002", startTime: 3, endTime: 6 }] },
  ],
  tracks: [
    {
      id: "T1",
      entityId: "CUP",
      shotId: "SHOT_002",
      startTime: 3,
      endTime: 5,
      samples: [
        { time: 3, frame: 75, bbox: { x: 0.1, y: 0.1, w: 0.1, h: 0.1 } },
        { time: 5, frame: 125, bbox: { x: 0.3, y: 0.5, w: 0.1, h: 0.1 } },
      ],
    },
  ],
} as unknown as VideoDNA;

describe("format", () => {
  it("formats BRL like the spec example", () => {
    expect(formatMoney(17.4)).toBe("R$ 17,40");
  });
  it("formats timeline time with tenths", () => {
    expect(formatTime(7.4)).toBe("00:07.4");
    expect(formatTime(65.25)).toBe("01:05.3");
  });
  it("formats bytes", () => {
    expect(formatBytes(1536)).toBe("1.5 KB");
  });
});

describe("dna helpers", () => {
  it("builds the character tree with hair before garments", () => {
    const tree = buildTree(dna);
    expect(tree.characters[0].children.map((c) => c.key)).toEqual(["HAIR", "SHIRT"]);
    expect(tree.scenery[0].children.map((c) => c.key)).toEqual(["WALL"]);
    expect(tree.objects.map((o) => o.key)).toEqual(["CUP"]);
  });
  it("inherits shots from the parent and the scene", () => {
    expect(shotsForEntity(dna, "SHIRT")).toEqual(["SHOT_001"]);
    expect(shotsForEntity(dna, "ENV")).toEqual(["SHOT_001", "SHOT_002"]);
    expect([...modifiedShots(dna)]).toEqual(["SHOT_001"]);
  });
  it("interpolates track boxes over time", () => {
    const [box] = visibleBoxes(dna, 4);
    expect(box.entityKey).toBe("CUP");
    expect(box.x).toBeCloseTo(0.2);
    expect(box.y).toBeCloseTo(0.3);
    expect(visibleBoxes(dna, 1)).toHaveLength(0);
  });
});

describe("SSE parser", () => {
  it("parses event, id and multi-line data", () => {
    expect(parseSseBlock('id: 3\nevent: progress\ndata: {"a":\ndata: 1}')).toEqual({
      id: "3",
      event: "progress",
      data: '{"a":\n1}',
    });
    expect(parseSseBlock(": keep-alive")).toEqual({});
  });
});
