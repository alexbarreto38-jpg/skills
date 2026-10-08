"use client";

import type {
  EditCreate,
  EntityOut,
  Job,
  JobEvent,
  ProjectSettings,
  QualityMode,
} from "@videodna/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api, streamJob, unwrap } from "./api";

const TERMINAL = new Set(["COMPLETED", "FAILED", "CANCELLED"]);

export const keys = {
  config: ["config"] as const,
  me: ["me"] as const,
  projects: ["projects"] as const,
  project: (id: string) => ["project", id] as const,
  dna: (id: string, view: string) => ["dna", id, view] as const,
  entities: (id: string) => ["entities", id] as const,
  edits: (id: string) => ["edits", id] as const,
  suggestions: (entityId: string, category: string) => ["suggestions", entityId, category] as const,
  estimate: (id: string) => ["estimate", id] as const,
  job: (id: string) => ["job", id] as const,
  outputs: (id: string) => ["outputs", id] as const,
  versions: (id: string) => ["versions", id] as const,
  costs: (id: string) => ["costs", id] as const,
  qa: (jobId: string) => ["qa", jobId] as const,
  jobs: (id: string) => ["jobs", id] as const,
};

// --- reads -------------------------------------------------------------------

export function useAppConfig() {
  return useQuery({
    queryKey: keys.config,
    queryFn: () => unwrap(api.GET("/config")),
    staleTime: 5 * 60_000,
  });
}

export function useProjects() {
  return useQuery({ queryKey: keys.projects, queryFn: () => unwrap(api.GET("/projects")) });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: keys.project(id),
    queryFn: () => unwrap(api.GET("/projects/{project_id}", { params: { path: { project_id: id } } })),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "ANALYZING" || status === "GENERATING" || status === "UPLOADED" ? 3000 : false;
    },
  });
}

export function useVideoDna(id: string, view: "current" | "original" = "current", enabled = true) {
  return useQuery({
    queryKey: keys.dna(id, view),
    queryFn: () =>
      unwrap(
        api.GET("/projects/{project_id}/video-dna", {
          params: { path: { project_id: id }, query: { view } },
        }),
      ),
    enabled,
  });
}

export function useEntities(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.entities(id),
    queryFn: () =>
      unwrap(api.GET("/projects/{project_id}/entities", { params: { path: { project_id: id } } })),
    enabled,
  });
}

export function useEditHistory(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.edits(id),
    queryFn: () =>
      unwrap(api.GET("/projects/{project_id}/edits", { params: { path: { project_id: id } } })),
    enabled,
  });
}

export function useSuggestions(entity: EntityOut | undefined, category: string | null) {
  return useQuery({
    queryKey: keys.suggestions(entity?.id ?? "-", category ?? "-"),
    queryFn: () =>
      unwrap(
        api.GET("/entities/{entity_id}/suggestions", {
          params: { path: { entity_id: entity!.id }, query: { category: category! } },
        }),
      ),
    enabled: !!entity && !!category,
    staleTime: 60_000,
  });
}

export function useCostEstimate(id: string, qualityMode: QualityMode, editCount: number, enabled = true) {
  return useQuery({
    queryKey: [...keys.estimate(id), qualityMode, editCount],
    queryFn: () =>
      unwrap(
        api.POST("/projects/{project_id}/cost-estimate", {
          params: { path: { project_id: id } },
          body: { qualityMode, renderKind: "preview" },
        }),
      ),
    enabled: enabled && editCount > 0,
    staleTime: 30_000,
  });
}

export function useOutputs(id: string, enabled = true) {
  return useQuery({
    queryKey: keys.outputs(id),
    queryFn: () =>
      unwrap(api.GET("/projects/{project_id}/outputs", { params: { path: { project_id: id } } })),
    enabled,
  });
}

export function useOutput(outputId: string | null | undefined) {
  return useQuery({
    queryKey: ["output", outputId],
    queryFn: () => unwrap(api.GET("/outputs/{output_id}", { params: { path: { output_id: outputId! } } })),
    enabled: !!outputId,
  });
}

export function useVersions(id: string) {
  return useQuery({
    queryKey: keys.versions(id),
    queryFn: () =>
      unwrap(api.GET("/projects/{project_id}/versions", { params: { path: { project_id: id } } })),
  });
}

export function useCosts(id: string) {
  return useQuery({
    queryKey: keys.costs(id),
    queryFn: () => unwrap(api.GET("/projects/{project_id}/costs", { params: { path: { project_id: id } } })),
  });
}

export function useProjectJobs(id: string, kind?: "ANALYSIS" | "GENERATION" | "PREVIEW" | "INGEST") {
  return useQuery({
    queryKey: [...keys.jobs(id), kind ?? "all"],
    queryFn: () =>
      unwrap(
        api.GET("/projects/{project_id}/jobs", {
          params: { path: { project_id: id }, query: kind ? { kind } : {} },
        }),
      ),
  });
}

export function useQaReports(jobId: string | null | undefined) {
  return useQuery({
    queryKey: keys.qa(jobId ?? "-"),
    queryFn: () => unwrap(api.GET("/jobs/{job_id}/qa", { params: { path: { job_id: jobId! } } })),
    enabled: !!jobId,
  });
}

export function useProviders() {
  return useQuery({ queryKey: ["providers"], queryFn: () => unwrap(api.GET("/providers")) });
}

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: () => unwrap(api.GET("/admin/metrics", { params: { query: { days: 30 } } })),
    refetchInterval: 15_000,
  });
}

/** Job status + live SSE events; falls back to polling if the stream drops. */
export function useJobStream(jobId: string | null | undefined) {
  const qc = useQueryClient();
  // Events are stored with the job they belong to, so switching jobs needs no
  // state reset inside the effect.
  const [stream, setStream] = useState<{ jobId: string | null; events: JobEvent[] }>({ jobId: null, events: [] });
  const events = stream.jobId === jobId ? stream.events : [];
  const job = useQuery({
    queryKey: keys.job(jobId ?? "-"),
    queryFn: () => unwrap(api.GET("/jobs/{job_id}", { params: { path: { job_id: jobId! } } })),
    enabled: !!jobId,
    refetchInterval: (query) => (query.state.data && TERMINAL.has(query.state.data.status) ? false : 4000),
  });

  useEffect(() => {
    if (!jobId) return;
    const controller = new AbortController();
    streamJob(
      jobId,
      (event) => {
        setStream((prev) =>
          prev.jobId === jobId ? { jobId, events: [...prev.events, event] } : { jobId, events: [event] },
        );
        qc.setQueryData<Job>(keys.job(jobId), (prev) =>
          prev
            ? {
                ...prev,
                status: event.status as Job["status"],
                stage: event.stage ?? prev.stage,
                progress: event.progress,
                message: event.message ?? prev.message,
              }
            : prev,
        );
      },
      controller.signal,
    )
      .then(() => qc.invalidateQueries({ queryKey: keys.job(jobId) }))
      .catch(() => {
        /* aborted or network error: polling keeps the status fresh */
      });
    return () => controller.abort();
  }, [jobId, qc]);

  return { job: job.data, events, isLoading: job.isLoading };
}

// --- writes ------------------------------------------------------------------

function useInvalidateProject(id: string) {
  const qc = useQueryClient();
  return () => {
    for (const key of [
      keys.project(id),
      ["dna", id],
      keys.entities(id),
      keys.edits(id),
      keys.estimate(id),
      ["suggestions"],
    ]) {
      qc.invalidateQueries({ queryKey: key });
    }
  };
}

export function useCreateEdit(id: string) {
  const invalidate = useInvalidateProject(id);
  return useMutation({
    mutationFn: (body: EditCreate) =>
      unwrap(api.POST("/projects/{project_id}/edits", { params: { path: { project_id: id } }, body })),
    onSuccess: invalidate,
  });
}

export function usePreviewImpact(id: string) {
  return useMutation({
    mutationFn: (body: EditCreate) =>
      unwrap(api.POST("/projects/{project_id}/impact", { params: { path: { project_id: id } }, body })),
  });
}

export function useUndoRedo(id: string) {
  const invalidate = useInvalidateProject(id);
  const undo = useMutation({
    mutationFn: () =>
      unwrap(api.POST("/projects/{project_id}/edits/undo", { params: { path: { project_id: id } } })),
    onSuccess: invalidate,
  });
  const redo = useMutation({
    mutationFn: () =>
      unwrap(api.POST("/projects/{project_id}/edits/redo", { params: { path: { project_id: id } } })),
    onSuccess: invalidate,
  });
  return { undo, redo };
}

export function useDeleteEdit(id: string) {
  const invalidate = useInvalidateProject(id);
  return useMutation({
    mutationFn: (editId: string) =>
      unwrap(
        api.DELETE("/projects/{project_id}/edits/{edit_id}", {
          params: { path: { project_id: id, edit_id: editId } },
        }),
      ),
    onSuccess: invalidate,
  });
}

export function useApplySuggestion(id: string) {
  const invalidate = useInvalidateProject(id);
  return useMutation({
    mutationFn: ({ suggestionId, instruction }: { suggestionId: string; instruction?: string }) =>
      unwrap(
        api.POST("/suggestions/{suggestion_id}/apply", {
          params: { path: { suggestion_id: suggestionId }, query: instruction ? { instruction } : {} },
        }),
      ),
    onSuccess: invalidate,
  });
}

export function useMoreSuggestions(entityId: string | undefined, category: string | null) {
  return useMutation({
    mutationFn: () =>
      unwrap(
        api.POST("/entities/{entity_id}/suggestions/more", {
          params: { path: { entity_id: entityId! }, query: { category: category! } },
        }),
      ),
  });
}

export function useSuggestionPreview() {
  return useMutation({
    mutationFn: (suggestionId: string) =>
      unwrap(
        api.POST("/suggestions/{suggestion_id}/preview", {
          params: { path: { suggestion_id: suggestionId } },
          body: {},
        }),
      ),
  });
}

export function useCorrectEntity(id: string) {
  const invalidate = useInvalidateProject(id);
  return useMutation({
    mutationFn: ({ entityId, property, value }: { entityId: string; property: "label" | "importance"; value: string }) =>
      unwrap(
        api.PATCH("/entities/{entity_id}", {
          params: { path: { entity_id: entityId } },
          body: { property, value },
        }),
      ),
    onSuccess: invalidate,
  });
}

export function useUpdateProject(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name?: string; settings?: ProjectSettings }) =>
      unwrap(api.PATCH("/projects/{project_id}", { params: { path: { project_id: id } }, body })),
    onSuccess: (project) => {
      qc.setQueryData(keys.project(id), project);
      qc.invalidateQueries({ queryKey: keys.estimate(id) });
      qc.invalidateQueries({ queryKey: keys.edits(id) });
    },
  });
}

export function useCreatePlan(id: string) {
  return useMutation({
    mutationFn: (body: { qualityMode: QualityMode; renderKind: "preview" | "final" }) =>
      unwrap(
        api.POST("/projects/{project_id}/generation-plan", { params: { path: { project_id: id } }, body }),
      ),
  });
}

export function useGenerate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ planId, idempotencyKey }: { planId: string; idempotencyKey: string }) =>
      unwrap(
        api.POST("/projects/{project_id}/generate", {
          params: { path: { project_id: id }, header: { "Idempotency-Key": idempotencyKey } },
          body: { planId },
        }),
      ),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.project(id) }),
  });
}

export function useCancelJob() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => unwrap(api.POST("/jobs/{job_id}/cancel", { params: { path: { job_id: jobId } } })),
    onSuccess: (job) => qc.setQueryData(keys.job(job.id), job),
  });
}

export function useCreateVersion(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      unwrap(api.POST("/projects/{project_id}/versions", { params: { path: { project_id: id } }, body: { name } })),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.versions(id) }),
  });
}

export function useRestoreVersion(id: string) {
  const invalidate = useInvalidateProject(id);
  return useMutation({
    mutationFn: (versionId: string) =>
      unwrap(
        api.POST("/projects/{project_id}/versions/{version_id}/restore", {
          params: { path: { project_id: id, version_id: versionId } },
        }),
      ),
    onSuccess: invalidate,
  });
}

/** Cria um projeto a partir do vídeo de exemplo e já inicia a análise. */
export function useCreateDemoProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (fresh: boolean = false) => unwrap(api.POST("/projects/demo", { body: { fresh } })),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.projects }),
  });
}

export function useDuplicateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(api.POST("/projects/{project_id}/duplicate", { params: { path: { project_id: id } } })),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.projects }),
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { response } = await api.DELETE("/projects/{project_id}", { params: { path: { project_id: id } } });
      if (!response.ok) throw new Error("Falha ao excluir");
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.projects }),
  });
}

export function useAnalyze(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (force: boolean) =>
      unwrap(api.POST("/projects/{project_id}/analyze", { params: { path: { project_id: id } }, body: { force } })),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.project(id) }),
  });
}
