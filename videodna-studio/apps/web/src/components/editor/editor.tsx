"use client";

import type { Project } from "@videodna/api-client";
import { ArrowLeft, Download, Redo2, Sparkles, Undo2, Wallet } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo } from "react";

import { MockBadge } from "@/components/app-header";
import { DnaTree } from "@/components/editor/dna-tree";
import { EntityInspector } from "@/components/editor/entity-inspector";
import { Player } from "@/components/editor/player";
import { ProjectPanel } from "@/components/editor/project-panel";
import { Timeline } from "@/components/editor/timeline";
import { ProjectSteps } from "@/components/project/project-steps";
import { Money } from "@/components/ui/money";
import { Button, IconButton, Spinner, cx } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { useEditor } from "@/lib/editor-store";
import { formatMoney } from "@/lib/format";
import { useHint } from "@/lib/hints";
import { QUALITY_MODE } from "@/lib/labels";
import {
  useCostEstimate,
  useEditHistory,
  useEntities,
  useProjectJobs,
  useQaReports,
  useUndoRedo,
  useVideoDna,
} from "@/lib/queries";

function CostPill({ project }: { project: Project }) {
  const mode = project.settings.qualityMode ?? "BALANCED";
  const { data, isFetching } = useCostEstimate(project.id, mode, project.editCount);
  if (!project.editCount) return null;
  const plan = data?.plan as { estimatedCostWithRepairs?: number; summary?: { affectedShots: number } } | undefined;
  return (
    <span
      className="flex items-center gap-2 rounded-lg border border-line bg-panel-2 px-3 py-1.5 text-xs"
      title={`Modo ${QUALITY_MODE[mode]?.label ?? mode} · pode chegar a ${formatMoney(plan?.estimatedCostWithRepairs, data?.currency)} se for preciso refazer trechos`}
    >
      <Wallet className="size-3.5 text-cyan" />
      {isFetching && !data ? (
        <Spinner className="size-3" />
      ) : (
        <>
          <span className="text-muted">Custo estimado:</span>
          <Money className="font-semibold" value={data?.estimatedCost} currency={data?.currency} />
          {plan?.summary && (
            <span className="text-faint">
              · {plan.summary.affectedShots} {plan.summary.affectedShots === 1 ? "cena" : "cenas"}
            </span>
          )}
        </>
      )}
    </span>
  );
}

export function Editor({ project }: { project: Project }) {
  const id = project.id;
  const dnaQuery = useVideoDna(id, "current");
  const entities = useEntities(id);
  const history = useEditHistory(id);
  const { undo, redo } = useUndoRedo(id);
  const generations = useProjectJobs(id, "GENERATION");
  const lastGeneration = generations.data?.find((j) => j.status === "COMPLETED");
  const qa = useQaReports(lastGeneration?.id);
  const { selectedKey, reset } = useEditor();
  // After the first change, point at the next step until the user gets there.
  const goReview = useHint("go-review", project.editCount > 0);
  const job = project.activeJob;
  const generating =
    job && job.kind === "GENERATION" && !["COMPLETED", "FAILED", "CANCELLED"].includes(job.status) ? job : null;

  useEffect(() => reset, [reset, id]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const target = e.target as HTMLElement;
      if (target.closest("input, textarea, select")) return;
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) redo.mutate();
        else undo.mutate();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo]);

  const dna = dnaQuery.data?.dna;
  const row = useMemo(() => entities.data?.find((e) => e.key === selectedKey), [entities.data, selectedKey]);
  const selected = useMemo(() => dna?.entities.find((e) => e.id === selectedKey), [dna, selectedKey]);

  if (dnaQuery.isLoading || !dna) {
    return (
      <div className="flex h-screen items-center justify-center gap-2 text-sm text-muted">
        <Spinner /> Carregando o Video DNA…
      </div>
    );
  }

  return (
    <div className="grid h-screen grid-rows-[56px_1fr_168px] overflow-hidden">
      <header className="flex items-center gap-3 border-b border-line bg-panel px-3">
        <Link href="/" className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs text-muted hover:bg-panel-3 hover:text-fg">
          <ArrowLeft className="size-3.5" /> Projetos
        </Link>
        <div className="min-w-0 max-w-56">
          <h1 className="truncate text-sm font-semibold" title={project.name}>
            {project.name}
          </h1>
        </div>
        <MockBadge />
        <div className="ml-2 flex items-center gap-0.5">
          <IconButton
            label="Desfazer (Ctrl+Z)"
            disabled={!history.data?.canUndo || undo.isPending}
            onClick={() => undo.mutate(undefined, { onError: (e) => toast.error("Erro", errorMessage(e)) })}
          >
            <Undo2 className="size-4" />
          </IconButton>
          <IconButton
            label="Refazer (Ctrl+Shift+Z)"
            disabled={!history.data?.canRedo || redo.isPending}
            onClick={() => redo.mutate(undefined, { onError: (e) => toast.error("Erro", errorMessage(e)) })}
          >
            <Redo2 className="size-4" />
          </IconButton>
        </div>
        <div className="flex flex-1 justify-center">
          <ProjectSteps project={project} route="project" compact className="hidden lg:block" />
        </div>
        {generating && (
          <Link
            href={`/projects/${id}/jobs/${generating.id}`}
            className="flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-1.5 text-xs hover:bg-accent/20"
            title="Mudanças feitas agora entram só na próxima geração"
          >
            <Spinner className="size-3" />
            Gerando seu vídeo… {Math.round(generating.progress ?? 0)}% · Ver progresso
          </Link>
        )}
        <CostPill project={project} />
        {project.latestOutputId && (
          <Link href={`/projects/${id}/result`}>
            <Button size="sm" variant="outline" icon={<Download className="size-3.5" />}>
              Resultado
            </Button>
          </Link>
        )}
        <Link
          href={`/projects/${id}/review`}
          onClick={(e) => {
            if (!project.editCount) e.preventDefault();
            else goReview.dismiss();
          }}
          title={project.editCount ? "Ver o que vai mudar e quanto custa, antes de gerar" : "Faça pelo menos uma alteração para continuar."}
        >
          <Button
            size="sm"
            variant="primary"
            icon={<Sparkles className="size-3.5" />}
            disabled={!project.editCount}
            className={cx(goReview.visible && "animate-pulse ring-2 ring-accent ring-offset-2 ring-offset-panel")}
          >
            Revisar e gerar
          </Button>
        </Link>
      </header>

      <div className="grid min-h-0 grid-cols-[264px_1fr_380px]">
        <aside className="min-h-0 overflow-y-auto border-r border-line bg-panel">
          <DnaTree dna={dna} editCount={project.editCount} isDemo={project.isDemo} />
        </aside>
        <main className="min-h-0 bg-bg">
          <Player
            src={project.sourceVideo?.proxyUrl}
            poster={project.sourceVideo?.posterUrl}
            dna={dna}
            showClickHint={project.editCount === 0 && !selectedKey}
          />
        </main>
        <aside className="min-h-0 overflow-y-auto border-l border-line bg-panel">
          {selected && row ? (
            <EntityInspector key={selected.id} projectId={id} row={row} entity={selected} dna={dna} history={history.data} />
          ) : (
            <ProjectPanel project={project} dna={dna} history={history.data} />
          )}
        </aside>
      </div>

      <footer className="border-t border-line bg-panel">
        <Timeline dna={dna} assetUrls={dnaQuery.data?.assetUrls ?? {}} qaReports={qa.data} />
      </footer>
    </div>
  );
}
