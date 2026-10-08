"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CheckCircle2, CircleAlert, Film } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppHeader } from "@/components/app-header";
import { JobProgress } from "@/components/project/job-progress";
import { Badge, Button } from "@/components/ui/primitives";
import { formatMoney, formatTime } from "@/lib/format";
import { GENERATION_STAGES } from "@/lib/labels";
import { keys, useJobStream, useQaReports } from "@/lib/queries";

/** Telas 6/7: geração por shot, QA automático e reparo localizado em tempo real. */
export default function JobPage() {
  const { id, jobId } = useParams<{ id: string; jobId: string }>();
  const qc = useQueryClient();
  const { job } = useJobStream(jobId);
  const done = job?.status === "COMPLETED";
  const qa = useQaReports(done || job?.status === "FAILED" ? jobId : null);
  const result = (job?.result ?? {}) as {
    actualCost?: number;
    estimatedCost?: number;
    currency?: string;
    needsAttention?: boolean;
    repairs?: number;
    unresolvedIssues?: { shotKey: string; description: string; start: number; end: number; message: string }[];
  };
  const issues = (qa.data ?? []).flatMap((r) => r.issues ?? []);

  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-4xl space-y-6 px-4 py-8">
        <Link href={`/projects/${id}`} className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-fg">
          <ArrowLeft className="size-3.5" /> Voltar ao editor
        </Link>
        <JobProgress
          jobId={jobId}
          stages={GENERATION_STAGES}
          title="Gerando seu vídeo"
          onFinished={() => {
            qc.invalidateQueries({ queryKey: keys.project(id) });
            qc.invalidateQueries({ queryKey: keys.outputs(id) });
          }}
        />

        {done && (
          <section className="panel space-y-4 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="flex items-center gap-2 text-base font-medium">
                {result.needsAttention ? (
                  <CircleAlert className="size-5 text-warn" />
                ) : (
                  <CheckCircle2 className="size-5 text-ok" />
                )}
                {result.needsAttention ? "Concluído com pontos de atenção" : "Vídeo gerado"}
              </p>
              <Link href={`/projects/${id}/result`}>
                <Button variant="primary" icon={<Film className="size-4" />}>
                  Comparar original × modificado
                </Button>
              </Link>
            </div>
            <div className="grid gap-3 text-sm sm:grid-cols-3">
              <p>
                <span className="block text-xs text-faint">Custo real</span>
                {formatMoney(result.actualCost, result.currency)}
                <span className="text-xs text-faint"> (estimado {formatMoney(result.estimatedCost, result.currency)})</span>
              </p>
              <p>
                <span className="block text-xs text-faint">Reparos localizados</span>
                {result.repairs ?? 0}
              </p>
              <p>
                <span className="block text-xs text-faint">Inconsistências restantes</span>
                {result.unresolvedIssues?.length ?? 0}
              </p>
            </div>
            {result.unresolvedIssues?.map((u) => (
              <p key={`${u.shotKey}${u.start}`} className="rounded-lg bg-warn/10 px-3 py-2 text-sm text-warn">
                {u.message} {u.shotKey} {formatTime(u.start)}–{formatTime(u.end)}: {u.description}
              </p>
            ))}
            {issues.length > 0 && (
              <div>
                <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-faint">QA automático</h3>
                <ul className="space-y-1.5">
                  {issues.map((i) => (
                    <li key={i.id} className="flex items-center gap-2 text-xs">
                      <Badge tone={i.status === "REPAIRED" ? "ok" : i.status === "UNRESOLVED" ? "bad" : "warn"}>
                        {i.status === "REPAIRED" ? "Corrigido" : i.status === "UNRESOLVED" ? "Pendente" : i.status}
                      </Badge>
                      <span className="font-mono text-faint">
                        {i.shotKey} {formatTime(i.startTime)}–{formatTime(i.endTime)}
                      </span>
                      <span className="text-muted">{i.description}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}
      </main>
    </div>
  );
}
