"use client";

import { useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, RefreshCw, Upload } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { AppHeader } from "@/components/app-header";
import { Editor } from "@/components/editor/editor";
import { DemoButton } from "@/components/project/demo-button";
import { JobProgress } from "@/components/project/job-progress";
import { ProjectSteps } from "@/components/project/project-steps";
import { UploadPanel } from "@/components/project/upload-panel";
import { Button, EmptyState, Spinner } from "@/components/ui/primitives";
import { LoadError } from "@/components/ui/server-offline";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { ANALYSIS_STAGES, REJECT_REASON } from "@/lib/labels";
import { keys, useAnalyze, useProject } from "@/lib/queries";
import { analysisRunning } from "@/lib/steps";

/** Routes a project to its current screen: upload → analysis (Tela 2) → editor (Tela 3/4). */
export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { data: project, isLoading, error, refetch } = useProject(id);
  const analyze = useAnalyze(id);
  const [replace, setReplace] = useState(false);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center gap-2 text-sm text-muted">
        <Spinner className="size-5" /> Abrindo o projeto…
      </div>
    );
  }
  if (error || !project) {
    return (
      <div className="min-h-screen">
        <AppHeader />
        <LoadError error={error} onRetry={() => refetch()} title="Projeto não encontrado" />
      </div>
    );
  }

  const running = analysisRunning(project);
  const analysisDone = project.analysis?.status === "COMPLETED";
  if (analysisDone && !running) return <Editor project={project} />;

  const source = project.sourceVideo;
  const needsUpload = !source || source.status === "PENDING_UPLOAD";
  const rejected = source?.status === "REJECTED";
  const lastJob = project.activeJob;
  const cancelled = !running && lastJob?.status === "CANCELLED";
  const state = needsUpload ? "normal" : rejected ? "rejected" : running ? "running" : cancelled ? "cancelled" : "failed";

  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <h1 className="mb-4 text-2xl font-semibold tracking-tight">{project.name}</h1>
        <ProjectSteps project={project} route="project" state={state} className="mb-6" />

        {needsUpload ? (
          <div className="panel space-y-4 p-5">
            <UploadPanel projectId={id} />
            <p className="text-center text-xs text-faint">
              Sem vídeo agora? <DemoButton variant="ghost" size="sm" />
            </p>
          </div>
        ) : running && lastJob ? (
          <JobProgress
            jobId={lastJob.id}
            stages={ANALYSIS_STAGES}
            title="Analisando seu vídeo"
            onFinished={() => {
              qc.invalidateQueries({ queryKey: keys.project(id) });
            }}
          />
        ) : (
          <div className="panel">
            <EmptyState
              icon={<AlertTriangle className="size-8 text-warn" />}
              title={rejected ? "Não deu para usar este vídeo" : cancelled ? "Análise cancelada" : "A análise não terminou"}
            >
              <p className="mb-4 max-w-md">
                {rejected
                  ? (REJECT_REASON[source?.errorCode ?? ""] ?? "Não deu para usar este arquivo. Tente outro vídeo.")
                  : cancelled
                    ? "Você cancelou a análise. Quando quiser, analise de novo."
                    : (lastJob?.errorMessage ?? "Algo interrompeu a análise.") +
                      " Tente de novo; se acontecer outra vez, envie outro vídeo."}
              </p>
              {rejected || replace ? (
                <div className="mx-auto max-w-md text-left">
                  <UploadPanel projectId={id} />
                </div>
              ) : (
                <div className="flex flex-wrap justify-center gap-2">
                  <Button
                    variant="primary"
                    icon={<RefreshCw className="size-4" />}
                    loading={analyze.isPending}
                    onClick={() =>
                      analyze.mutate(true, {
                        onError: (e) => toast.error("Não foi possível analisar de novo", errorMessage(e)),
                      })
                    }
                  >
                    Analisar de novo
                  </Button>
                  <Button variant="outline" icon={<Upload className="size-4" />} onClick={() => setReplace(true)}>
                    Enviar outro vídeo
                  </Button>
                </div>
              )}
            </EmptyState>
          </div>
        )}
      </main>
    </div>
  );
}
