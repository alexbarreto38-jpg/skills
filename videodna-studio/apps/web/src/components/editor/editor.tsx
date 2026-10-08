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
import { Badge, Button, IconButton, Kbd, Spinner, statusTone } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { useEditor } from "@/lib/editor-store";
import { formatMoney } from "@/lib/format";
import { PROJECT_STATUS, QUALITY_MODE, label } from "@/lib/labels";
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
  if (!project.editCount) {
    return <span className="text-xs text-faint">Sem alterações</span>;
  }
  const plan = data?.plan as { estimatedCostWithRepairs?: number; summary?: { affectedShots: number } } | undefined;
  return (
    <span
      className="flex items-center gap-2 rounded-lg border border-line bg-panel-2 px-3 py-1.5 text-xs"
      title={`Modo ${QUALITY_MODE[mode]?.label ?? mode} · até ${formatMoney(plan?.estimatedCostWithRepairs, data?.currency)} com reparos`}
    >
      <Wallet className="size-3.5 text-cyan" />
      {isFetching && !data ? (
        <Spinner className="size-3" />
      ) : (
        <>
          <span className="text-muted">Estimativa:</span>
          <span className="font-semibold">{formatMoney(data?.estimatedCost, data?.currency)}</span>
          {plan?.summary && <span className="text-faint">· {plan.summary.affectedShots} shots</span>}
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
        <div className="min-w-0">
          <h1 className="truncate text-sm font-semibold">{project.name}</h1>
        </div>
        <Badge tone={statusTone(project.status)}>{label(PROJECT_STATUS, project.status)}</Badge>
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
        <div className="flex-1" />
        <span className="hidden items-center gap-1 text-[11px] text-faint xl:flex">
          <Kbd>Ctrl</Kbd>+<Kbd>Z</Kbd> desfazer
        </span>
        <CostPill project={project} />
        {project.latestOutputId && (
          <Link href={`/projects/${id}/result`}>
            <Button size="sm" variant="outline" icon={<Download className="size-3.5" />}>
              Resultado
            </Button>
          </Link>
        )}
        <Link href={`/projects/${id}/review`}>
          <Button size="sm" variant="primary" icon={<Sparkles className="size-3.5" />} disabled={!project.editCount}>
            Revisar e gerar
          </Button>
        </Link>
      </header>

      <div className="grid min-h-0 grid-cols-[264px_1fr_380px]">
        <aside className="min-h-0 overflow-y-auto border-r border-line bg-panel">
          <DnaTree dna={dna} />
        </aside>
        <main className="min-h-0 bg-bg">
          <Player src={project.sourceVideo?.proxyUrl} poster={project.sourceVideo?.posterUrl} dna={dna} />
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
