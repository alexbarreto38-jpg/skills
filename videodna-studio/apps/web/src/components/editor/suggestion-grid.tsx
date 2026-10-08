"use client";

import type { EntityOut, ImpactReport, Suggestion } from "@videodna/api-client";
import { ImageIcon, Plus, Sparkles, Wand2, X } from "lucide-react";
import { useState } from "react";

import { ImpactCard } from "@/components/editor/impact-card";
import { useDemoMode } from "@/components/ui/money";
import { Badge, Button, EmptyState, Spinner, cx } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import {
  useApplySuggestion,
  useJobStream,
  useMoreSuggestions,
  useOutput,
  usePreviewImpact,
  useSuggestionPreview,
  useSuggestions,
} from "@/lib/queries";

function FramePreview({ jobId, onClose }: { jobId: string; onClose: () => void }) {
  const demo = useDemoMode();
  const { job } = useJobStream(jobId);
  const outputId = job?.status === "COMPLETED" ? (job.result?.outputId as string | undefined) : undefined;
  const { data: output } = useOutput(outputId);
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-black">
      {output ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={output.url} alt="Preview no frame" className="w-full" />
      ) : job?.status === "FAILED" ? (
        <p className="p-3 text-xs text-bad">{job.errorMessage}</p>
      ) : (
        <div className="flex aspect-video items-center justify-center gap-2 text-xs text-muted">
          <Spinner /> Preparando a prévia no quadro…
        </div>
      )}
      <div className="flex items-center justify-between bg-panel-2 px-3 py-1.5">
        <span className="text-[11px] text-muted">
          {demo ? "Prévia simulada num quadro do seu vídeo" : "Um quadro do seu vídeo com a mudança aplicada"}
        </span>
        <button type="button" className="text-[11px] text-muted hover:text-fg" onClick={onClose}>
          Fechar
        </button>
      </div>
    </div>
  );
}

export function SuggestionGrid({
  projectId,
  entity,
  category,
  display,
  instruction,
  onApplied,
}: {
  projectId: string;
  entity: EntityOut;
  category: string;
  display: "cards" | "swatches";
  instruction: string;
  onApplied?: () => void;
}) {
  const { data, isLoading, error } = useSuggestions(entity, category);
  const more = useMoreSuggestions(entity.id, category);
  const apply = useApplySuggestion(projectId);
  const impactQuery = usePreviewImpact(projectId);
  const preview = useSuggestionPreview();
  const [extra, setExtra] = useState<Suggestion[]>([]);
  const [selected, setSelected] = useState<Suggestion | null>(null);
  const [impact, setImpact] = useState<ImpactReport | null>(null);
  const [previewJob, setPreviewJob] = useState<string | null>(null);

  const items = [...(data?.items ?? []), ...extra];

  function choose(s: Suggestion) {
    setSelected(s);
    setImpact(null);
    impactQuery.mutate(
      { entityKey: entity.key, op: s.op, property: s.property, newValue: s.value, source: "suggestion" },
      { onSuccess: setImpact },
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center gap-2 py-10 text-xs text-muted">
        <Spinner /> Preparando opções que combinam com a cena…
      </div>
    );
  }
  if (error) return <EmptyState title="Sem sugestões">{errorMessage(error)}</EmptyState>;

  return (
    <div className="space-y-3">
      <div className={cx("grid gap-2", display === "swatches" ? "grid-cols-4" : "grid-cols-2")}>
        {items.map((s) => {
          const isSelected = selected?.id === s.id;
          const incompatible = s.tags?.some((t) => t.startsWith("incompatível"));
          return (
            <button
              key={s.id}
              type="button"
              onClick={() => choose(s)}
              aria-label={s.label}
              aria-pressed={isSelected}
              className={cx(
                "group relative overflow-hidden rounded-xl border text-left transition-all",
                isSelected ? "border-accent ring-2 ring-accent/40" : "border-line hover:border-line-strong",
              )}
              title={s.tags?.join(" · ")}
            >
              {s.previewUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={s.previewUrl} alt="" className={cx("w-full bg-panel-3", display === "swatches" ? "aspect-square object-cover" : "aspect-[256/300]")} />
              ) : (
                <div className="flex aspect-square items-center justify-center bg-panel-3 text-faint">
                  <ImageIcon className="size-6" />
                </div>
              )}
              {display === "cards" ? null : (
                <span className="block truncate px-1.5 py-1 text-[11px] text-muted">{s.label}</span>
              )}
              {isSelected && (
                <span className="absolute right-1.5 top-1.5">
                  <Badge tone="accent">Escolhido</Badge>
                </span>
              )}
              {incompatible && (
                <span className="absolute left-1.5 top-1.5" title="Pode não combinar com o que acontece na cena">
                  <Badge tone="warn">atenção</Badge>
                </span>
              )}
            </button>
          );
        })}
      </div>

      <Button
        size="sm"
        variant="ghost"
        className="w-full"
        icon={<Plus className="size-3.5" />}
        loading={more.isPending}
        onClick={() =>
          more.mutate(undefined, {
            onSuccess: (page) => setExtra((prev) => [...prev, ...page.items]),
            onError: (e) => toast.error("Sem mais opções", errorMessage(e)),
          })
        }
      >
        Gerar mais opções
      </Button>

      {selected && (
        // Sticky at the bottom of the inspector: choosing a card is not applying it,
        // and the button to apply must be on screen without scrolling.
        <div className="sticky bottom-0 z-10 -mx-4 space-y-2 border-t border-accent/40 bg-panel px-4 pb-4 pt-3 shadow-[0_-8px_16px_rgba(0,0,0,.35)]">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm">
              Você escolheu <span className="font-medium">“{selected.label}”</span>.{" "}
              <span className="text-muted">Ainda não foi aplicado.</span>
            </p>
            <button
              type="button"
              aria-label="Cancelar a escolha"
              className="text-muted hover:text-fg"
              onClick={() => {
                setSelected(null);
                setPreviewJob(null);
              }}
            >
              <X className="size-4" />
            </button>
          </div>
          {impact ? <ImpactCard impact={impact} /> : impactQuery.isPending && <Spinner />}
          {previewJob && <FramePreview jobId={previewJob} onClose={() => setPreviewJob(null)} />}
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              className="flex-1"
              icon={<Wand2 className="size-3.5" />}
              loading={preview.isPending}
              title="Mostra a mudança aplicada num quadro do vídeo, antes de gerar"
              onClick={() =>
                preview.mutate(selected.id, {
                  onSuccess: (job) => setPreviewJob(job.id),
                  onError: (e) => toast.error("Prévia indisponível", errorMessage(e)),
                })
              }
            >
              Ver no quadro
            </Button>
            <Button
              size="sm"
              variant="primary"
              className="flex-1"
              icon={<Sparkles className="size-3.5" />}
              disabled={impact?.warnings?.some((w) => w.blocking)}
              loading={apply.isPending}
              onClick={() =>
                apply.mutate(
                  { suggestionId: selected.id, instruction: instruction.trim() || undefined },
                  {
                    onSuccess: () => {
                      toast.ok(
                        `Mudança aplicada: ${selected.label}`,
                        "Ela aparece no vídeo quando você gerar. Continue mudando ou clique em “Revisar e gerar”.",
                      );
                      setSelected(null);
                      onApplied?.();
                    },
                    onError: (e) => toast.error("Não foi possível aplicar", errorMessage(e)),
                  },
                )
              }
            >
              Aplicar mudança
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
