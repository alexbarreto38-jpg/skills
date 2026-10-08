"use client";

import type { EditHistory, Project, ProjectSettings, VideoDNA } from "@videodna/api-client";
import { BookOpen, CircleHelp, Trash2 } from "lucide-react";

import { Badge, EmptyState, IconButton, SectionTitle, Switch, impactTone } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { useEditor } from "@/lib/editor-store";
import { formatTime } from "@/lib/format";
import { IMPACT, OP_LABEL, label } from "@/lib/labels";
import { useDeleteEdit, useUpdateProject } from "@/lib/queries";

const LOCKS: { key: keyof NonNullable<ProjectSettings["locks"]>; label: string; description: string }[] = [
  { key: "story", label: "LOCK STORY", description: "Preserva a estrutura narrativa (copo → prato continua quebrando)." },
  { key: "camera", label: "LOCK CAMERA", description: "Ângulo, movimento, distância e cortes originais." },
  { key: "motion", label: "LOCK MOTION", description: "Poses, gestos, caminhada e interações." },
  { key: "audio", label: "LOCK AUDIO", description: "Mantém o áudio original." },
  { key: "timing", label: "LOCK TIMING", description: "Preserva duração e ritmo de cada shot." },
];

/** Inspector when nothing is selected: story, structural locks, edit history. */
export function ProjectPanel({ project, dna, history }: { project: Project; dna: VideoDNA; history?: EditHistory }) {
  const update = useUpdateProject(project.id);
  const remove = useDeleteEdit(project.id);
  const { select, seek } = useEditor();
  const settings = project.settings;
  const locks = settings.locks ?? {};
  const review = dna.entities.filter((e) => e.needsReview);
  const edits = (history?.edits ?? []).filter((e) => e.state === "ACTIVE");
  const name = (key: string | null | undefined) => dna.entities.find((e) => e.id === key)?.label ?? key ?? "Projeto";

  function setLock(key: string, value: boolean) {
    update.mutate(
      { settings: { ...settings, locks: { ...locks, [key]: value } } },
      { onError: (e) => toast.error("Não foi possível salvar", errorMessage(e)) },
    );
  }

  return (
    <div className="space-y-6 p-4">
      {dna.narrative && (
        <section className="space-y-2">
          <SectionTitle>
            <span className="flex items-center gap-1.5">
              <BookOpen className="size-3" /> História
            </span>
          </SectionTitle>
          <p className="text-sm leading-relaxed text-fg/90">{dna.narrative.summary}</p>
          <ol className="mt-2 space-y-1">
            {dna.narrative.beats?.map((b) => (
              <li key={b.id}>
                <button
                  type="button"
                  onClick={() => seek(b.startTime + 0.05)}
                  className="flex w-full gap-2 rounded-md px-1.5 py-1 text-left hover:bg-panel-3"
                >
                  <span className="w-11 shrink-0 font-mono text-[10px] leading-5 text-faint">{formatTime(b.startTime)}</span>
                  <span className="min-w-0">
                    <span className="block text-xs text-fg/90">{b.description}</span>
                    <span className="block font-mono text-[10px] text-cyan/80">{b.abstract}</span>
                  </span>
                </button>
              </li>
            ))}
          </ol>
        </section>
      )}

      {review.length > 0 && (
        <section>
          <SectionTitle>Precisa de revisão</SectionTitle>
          <ul className="space-y-1">
            {review.map((e) => (
              <li key={e.id}>
                <button
                  type="button"
                  onClick={() => select(e.id)}
                  className="flex w-full items-center gap-2 rounded-lg border border-warn/30 bg-warn/5 px-2.5 py-2 text-left text-xs hover:bg-warn/10"
                >
                  <CircleHelp className="size-3.5 text-warn" />
                  <span className="min-w-0 flex-1 truncate">
                    {[e.label, ...(e.alternatives ?? []).map((a) => a.label)].join(" / ")}?
                  </span>
                  <span className="font-mono text-faint">{(e.confidence * 100).toFixed(0)}%</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="space-y-3">
        <SectionTitle>Restrições estruturais</SectionTitle>
        {LOCKS.map((l) => (
          <Switch
            key={l.key}
            label={l.label}
            description={l.description}
            checked={locks[l.key] ?? true}
            disabled={update.isPending}
            onChange={(v) => setLock(l.key, v)}
          />
        ))}
      </section>

      <section>
        <SectionTitle>Alterações ({edits.length})</SectionTitle>
        {edits.length === 0 ? (
          <EmptyState title="Nenhuma alteração ainda">
            Clique em um personagem, objeto ou no cenário — na árvore ou direto no vídeo — para ver as opções.
          </EmptyState>
        ) : (
          <ul className="space-y-1.5">
            {edits.map((e) => {
              const impact = e.impact as { level?: string } | undefined;
              return (
                <li key={e.id} className="flex items-center gap-2 rounded-lg bg-panel-2 px-2.5 py-2 text-xs">
                  <Badge tone={impactTone(impact?.level)}>{label(IMPACT, impact?.level).replace("Impacto ", "")}</Badge>
                  <button type="button" className="min-w-0 flex-1 truncate text-left hover:text-white" onClick={() => e.entityKey && select(e.entityKey)}>
                    <span className="text-muted">{label(OP_LABEL, e.op)} · </span>
                    {name(e.entityKey)}
                  </button>
                  <IconButton label="Remover alteração" onClick={() => remove.mutate(e.id)}>
                    <Trash2 className="size-3.5" />
                  </IconButton>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
