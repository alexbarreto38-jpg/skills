"use client";

import { useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { useParams } from "next/navigation";

import { AppHeader } from "@/components/app-header";
import { Editor } from "@/components/editor/editor";
import { JobProgress } from "@/components/project/job-progress";
import { UploadPanel } from "@/components/project/upload-panel";
import { Button, EmptyState, Spinner } from "@/components/ui/primitives";
import { errorMessage } from "@/lib/api";
import { ANALYSIS_STAGES } from "@/lib/labels";
import { keys, useAnalyze, useProject } from "@/lib/queries";

/** Routes a project to its current screen: upload → analysis (Tela 2) → editor (Tela 3/4). */
export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const { data: project, isLoading, error } = useProject(id);
  const analyze = useAnalyze(id);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (error || !project) {
    return (
      <div className="min-h-screen">
        <AppHeader />
        <EmptyState title="Projeto não encontrado">{errorMessage(error)}</EmptyState>
      </div>
    );
  }

  const activeAnalysis =
    project.activeJob && ["ANALYSIS", "INGEST"].includes(project.activeJob.kind) ? project.activeJob : null;
  const analysisDone = project.analysis?.status === "COMPLETED";

  if (analysisDone && !activeAnalysis) return <Editor project={project} />;

  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="mb-1 text-2xl font-semibold tracking-tight">{project.name}</h1>
        {!project.sourceVideo || project.sourceVideo.status === "PENDING_UPLOAD" ? (
          <>
            <p className="mb-6 text-sm text-muted">Envie o vídeo de referência para começar.</p>
            <div className="panel p-5">
              <UploadPanel projectId={id} />
            </div>
          </>
        ) : activeAnalysis ? (
          <>
            <p className="mb-6 text-sm text-muted">
              Analisando seu vídeo — FFmpeg cuida da parte técnica, modelos de IA da parte semântica.
            </p>
            <JobProgress
              jobId={activeAnalysis.id}
              stages={ANALYSIS_STAGES}
              title="Analisando seu vídeo"
              onFinished={() => {
                qc.invalidateQueries({ queryKey: keys.project(id) });
              }}
            />
          </>
        ) : (
          <div className="panel mt-6">
            <EmptyState icon={<AlertTriangle className="size-8 text-warn" />} title="A análise não foi concluída">
              <p className="mb-4">
                {project.sourceVideo.status === "REJECTED"
                  ? `O vídeo foi recusado (${project.sourceVideo.errorCode}). Envie outro arquivo.`
                  : "Você pode tentar analisar novamente."}
              </p>
              {project.sourceVideo.status === "REJECTED" ? (
                <UploadPanel projectId={id} />
              ) : (
                <Button
                  variant="primary"
                  icon={<RefreshCw className="size-4" />}
                  loading={analyze.isPending}
                  onClick={() => analyze.mutate(true)}
                >
                  Analisar novamente
                </Button>
              )}
            </EmptyState>
          </div>
        )}
      </main>
    </div>
  );
}
