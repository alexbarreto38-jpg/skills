"use client";

import type { EditHistory, Project, ProjectSettings, VideoDNA } from "@videodna/api-client";
import { BookOpen, ChevronRight, CircleHelp, Lightbulb, SlidersHorizontal, Trash2 } from "lucide-react";

import { DemoNotice } from "@/components/ui/demo-notice";
import { Hint } from "@/components/ui/hint";
import { Badge, IconButton, SectionTitle, Switch, impactTone } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { useEditor } from "@/lib/editor-store";
import { formatTime } from "@/lib/format";
import { resetHints, useAnyHintDismissed } from "@/lib/hints";
import { IMPACT, OP_LABEL, label } from "@/lib/labels";
import { useDeleteEdit, useUpdateProject } from "@/lib/queries";

/** What stays the same as the original ("locks"), in the user's words. */
const KEEP: { key: keyof NonNullable<ProjectSettings["locks"]>; label: string; description: string }[] = [
  {
    key: "story",
    label: "Manter a história",
    description: "As ações principais continuam acontecendo (ex.: se o copo virar prato, o prato ainda cai e quebra).",
  },
  { key: "camera", label: "Manter a câmera", description: "Mesmo ângulo, movimento e cortes." },
  { key: "motion", label: "Manter os movimentos", description: "Mesmas poses, gestos e caminhadas." },
  { key: "audio", label: "Manter o som", description: "O áudio original continua igual." },
  { key: "timing", label: "Manter o tempo", description: "Cada cena dura exatamente o mesmo." },
];

const IMPACT_SHORT: Record<string, string> = { NONE: "nenhum", LOW: "pequena", MEDIUM: "média", HIGH: "grande" };

/** Right panel when nothing is selected: how to edit, the user's changes, the story, advanced options. */
export function ProjectPanel({ project, dna, history }: { project: Project; dna: VideoDNA; history?: EditHistory }) {
  const update = useUpdateProject(project.id);
  const remove = useDeleteEdit(project.id);
  const { select, seek } = useEditor();
  const hintsDismissed = useAnyHintDismissed();
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
      <Hint id="how-to-edit" active={edits.length === 0}>
        <p className="mb-1.5 font-medium">Como editar seu vídeo</p>
        <ol className="list-decimal space-y-1 pl-4 text-muted">
          <li>Clique em uma pessoa, roupa, objeto ou no cenário — na lista à esquerda ou direto no vídeo.</li>
          <li>Escolha uma das opções que aparecem aqui e clique em “Aplicar mudança”.</li>
          <li>Quando terminar, clique em “Revisar e gerar”, no canto superior direito.</li>
        </ol>
      </Hint>
      <Hint id="go-review" active={edits.length > 0}>
        Pronto para ver o resultado? Clique em “Revisar e gerar”, no canto superior direito. Você ainda pode fazer
        outras mudanças antes.
      </Hint>

      {review.length > 0 && (
        <section>
          <SectionTitle>Confirme o que é</SectionTitle>
          <p className="mb-2 text-xs leading-relaxed text-muted">
            A IA não tem certeza destes itens. Clique em cada um e confirme (ou corrija) — assim nada é trocado pela
            coisa errada.
          </p>
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
                    É {[e.label, ...(e.alternatives ?? []).map((a) => a.label)].join(" ou ")}?
                  </span>
                  <span className="text-faint" title="Quanto a IA tem certeza">
                    {(e.confidence * 100).toFixed(0)}% de certeza
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section>
        <SectionTitle>Suas mudanças ({edits.length})</SectionTitle>
        {edits.length === 0 ? (
          <p className="text-xs text-muted">Nenhuma ainda. Elas aparecem aqui assim que você aplicar a primeira.</p>
        ) : (
          <ul className="space-y-1.5">
            {edits.map((e) => {
              const impact = e.impact as { level?: string } | undefined;
              return (
                <li key={e.id} className="flex items-center gap-2 rounded-lg bg-panel-2 px-2.5 py-2 text-xs">
                  <span title={label(IMPACT, impact?.level)}>
                    <Badge tone={impactTone(impact?.level)}>{IMPACT_SHORT[impact?.level ?? ""] ?? "—"}</Badge>
                  </span>
                  <button
                    type="button"
                    className="min-w-0 flex-1 truncate text-left hover:text-white"
                    onClick={() => e.entityKey && select(e.entityKey)}
                  >
                    <span className="text-muted">{label(OP_LABEL, e.op)} · </span>
                    {name(e.entityKey)}
                  </button>
                  <IconButton label="Desfazer esta mudança" onClick={() => remove.mutate(e.id)}>
                    <Trash2 className="size-3.5" />
                  </IconButton>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {dna.narrative && (
        <section className="space-y-2">
          <SectionTitle>
            <span className="flex items-center gap-1.5">
              <BookOpen className="size-3" /> O que acontece no vídeo
            </span>
          </SectionTitle>
          {project.analysis?.mock && !project.isDemo && <DemoNotice variant="editor" />}
          <p className="text-sm leading-relaxed text-fg/90">{dna.narrative.summary}</p>
          <ol className="mt-2 space-y-1">
            {dna.narrative.beats?.map((b) => (
              <li key={b.id}>
                <button
                  type="button"
                  onClick={() => seek(b.startTime + 0.05)}
                  title="Ir para este momento do vídeo"
                  className="flex w-full gap-2 rounded-md px-1.5 py-1 text-left hover:bg-panel-3"
                >
                  <span className="w-11 shrink-0 font-mono text-[10px] leading-5 text-faint">{formatTime(b.startTime)}</span>
                  <span className="min-w-0 text-xs text-fg/90">{b.description}</span>
                </button>
              </li>
            ))}
          </ol>
        </section>
      )}

      <details className="group rounded-xl border border-line">
        <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2.5 text-xs font-medium text-muted hover:text-fg [&::-webkit-details-marker]:hidden">
          <SlidersHorizontal className="size-3.5" />
          <span className="flex-1">Opções avançadas</span>
          <ChevronRight className="size-3.5 transition-transform group-open:rotate-90" />
        </summary>
        <div className="space-y-3 border-t border-line p-3">
          <p className="text-xs leading-relaxed text-muted">
            <span className="font-medium text-fg">O que manter igual ao original.</span> Tudo vem ligado: a IA só
            muda o que você pedir. Desligue um item apenas se quiser que ele também possa mudar.
          </p>
          {KEEP.filter((l) => l.key !== "audio" || dna.technical.hasAudio).map((l) => (
            <Switch
              key={l.key}
              label={l.label}
              description={l.description}
              checked={locks[l.key] ?? true}
              disabled={update.isPending}
              onChange={(v) => setLock(l.key, v)}
            />
          ))}
        </div>
      </details>

      {hintsDismissed && (
        <button
          type="button"
          onClick={resetHints}
          className="flex items-center gap-1.5 text-xs text-muted hover:text-fg"
        >
          <Lightbulb className="size-3.5" /> Mostrar dicas de novo
        </button>
      )}
    </div>
  );
}
