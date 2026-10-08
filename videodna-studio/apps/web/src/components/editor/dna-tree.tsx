"use client";

import type { VideoDNA } from "@videodna/api-client";
import { ChevronRight, CircleHelp, Clapperboard, Music2, Type, Zap } from "lucide-react";
import { useMemo, useState } from "react";

import { EntityIcon } from "@/components/editor/entity-icon";
import { Hint } from "@/components/ui/hint";
import { SectionTitle, cx } from "@/components/ui/primitives";
import { type TreeNode, buildTree, isModified, shotsForEntity } from "@/lib/dna";
import { useEditor } from "@/lib/editor-store";
import { formatTime } from "@/lib/format";
import { WARDROBE_SLOT } from "@/lib/labels";

function NodeRow({ node, dna, depth = 0 }: { node: TreeNode; dna: VideoDNA; depth?: number }) {
  const { selectedKey, select, seek } = useEditor();
  const [open, setOpen] = useState(depth === 0);
  const e = node.entity;
  const selected = selectedKey === e.id;
  const hint = e.type === "wardrobe" ? WARDROBE_SLOT[e.subtype ?? ""] : undefined;
  return (
    <li>
      <div
        className={cx(
          "group flex h-8 cursor-pointer items-center gap-1.5 rounded-md pr-2 text-[13px] transition-colors",
          selected ? "bg-accent-soft text-white" : "text-fg/90 hover:bg-panel-3",
          e.edit?.removed && "line-through opacity-60",
        )}
        style={{ paddingLeft: 6 + depth * 14 }}
        onClick={() => {
          select(e.id);
          const first = shotsForEntity(dna, e.id)[0];
          const shot = dna.shots.find((s) => s.id === first);
          const appearance = e.appearances?.[0];
          if (appearance) seek(appearance.startTime + 0.05);
          else if (shot) seek(shot.startTime + 0.05);
        }}
      >
        {node.children.length ? (
          <button
            type="button"
            aria-label={open ? "Recolher" : "Expandir"}
            onClick={(ev) => {
              ev.stopPropagation();
              setOpen(!open);
            }}
            className="text-faint hover:text-fg"
          >
            <ChevronRight className={cx("size-3.5 transition-transform", open && "rotate-90")} />
          </button>
        ) : (
          <span className="w-3.5" />
        )}
        <span className={cx(selected ? "text-white" : "text-muted")}>
          <EntityIcon type={e.type} subtype={e.subtype} />
        </span>
        <span className="min-w-0 flex-1 truncate" title={hint ? `${hint}: ${e.label}` : e.label}>
          {e.label}
        </span>
        {e.needsReview && (
          <span title="A IA não tem certeza do que é este item: clique para confirmar">
            <CircleHelp className="size-3.5 shrink-0 text-warn" aria-label="Confirmar o que é" />
          </span>
        )}
        {e.importance === "ESSENTIAL" && (
          <span className="rounded bg-accent-soft px-1 text-[9px] font-semibold text-[#c9bcff]" title="Essencial para a história">
            E
          </span>
        )}
        {isModified(e) && <span className="size-1.5 shrink-0 rounded-full bg-accent" title="Modificado" />}
      </div>
      {open && node.children.length > 0 && (
        <ul>
          {node.children.map((child) => (
            <NodeRow key={child.key} node={child} dna={dna} depth={depth + 1} />
          ))}
        </ul>
      )}
    </li>
  );
}

export function DnaTree({ dna, editCount = 0, isDemo = false }: { dna: VideoDNA; editCount?: number; isDemo?: boolean }) {
  const tree = useMemo(() => buildTree(dna), [dna]);
  const { seek, selectedKey } = useEditor();
  return (
    <div className="space-y-5 p-3">
      <Hint id="pick-element" active={editCount === 0 && !selectedKey}>
        {isDemo
          ? "Comece por aqui: clique em um elemento, como “Menino” ou “Copo de vidro”, para ver o que dá para mudar."
          : "Comece por aqui: clique em um personagem, objeto ou no cenário para ver o que dá para mudar."}
      </Hint>
      <section>
        <SectionTitle>Personagens</SectionTitle>
        <ul>
          {tree.characters.map((n) => (
            <NodeRow key={n.key} node={n} dna={dna} />
          ))}
        </ul>
      </section>
      <section>
        <SectionTitle>Cenário</SectionTitle>
        <ul>
          {tree.scenery.map((n) => (
            <NodeRow key={n.key} node={n} dna={dna} />
          ))}
        </ul>
      </section>
      <section>
        <SectionTitle>Objetos</SectionTitle>
        <ul>
          {tree.objects.map((n) => (
            <NodeRow key={n.key} node={n} dna={dna} />
          ))}
        </ul>
      </section>
      <section>
        <SectionTitle>Ações</SectionTitle>
        <ul className="space-y-0.5">
          {dna.actions.map((a) => (
            <li key={a.id}>
              <button
                type="button"
                onClick={() => seek(a.startTime + 0.05)}
                className="flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-left text-[13px] text-fg/90 hover:bg-panel-3"
              >
                <Zap className={cx("size-3.5 shrink-0", a.essential ? "text-accent" : "text-faint")} />
                <span className="min-w-0 flex-1 truncate">{a.label}</span>
                <span className="font-mono text-[10px] text-faint">{formatTime(a.startTime)}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>
      <section>
        <SectionTitle>Áudio</SectionTitle>
        <ul className="space-y-0.5">
          {dna.audio.segments
            ?.filter((s) => s.kind !== "ambience")
            .map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => seek(s.startTime)}
                  className="flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-left text-[13px] text-fg/90 hover:bg-panel-3"
                  title={s.transcript ?? s.label ?? s.kind}
                >
                  <Music2 className="size-3.5 shrink-0 text-cyan" />
                  <span className="min-w-0 flex-1 truncate">{s.transcript ? `“${s.transcript}”` : s.label}</span>
                  <span className="font-mono text-[10px] text-faint">{formatTime(s.startTime)}</span>
                </button>
              </li>
            ))}
        </ul>
      </section>
      {(dna.onScreenText?.length ?? 0) > 0 && (
        <section>
          <SectionTitle>Texto em tela</SectionTitle>
          <ul className="space-y-0.5">
            {dna.onScreenText!.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  onClick={() => seek(t.startTime)}
                  className="flex w-full items-center gap-2 rounded-md px-1.5 py-1 text-left text-[13px] text-fg/90 hover:bg-panel-3"
                  title="Texto detectado por OCR — não é alterado automaticamente"
                >
                  <Type className="size-3.5 shrink-0 text-muted" />
                  <span className="min-w-0 flex-1 truncate">{t.text}</span>
                  <span className="text-[10px] text-faint">{(t.confidence * 100).toFixed(0)}%</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
      <section>
        <SectionTitle>Shots</SectionTitle>
        <p className="flex items-center gap-2 px-1.5 text-xs text-muted">
          <Clapperboard className="size-3.5" /> {dna.shots.length} shots · {dna.scenes.length} cena(s)
        </p>
      </section>
    </div>
  );
}
