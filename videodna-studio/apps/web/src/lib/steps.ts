import type { Project } from "@videodna/api-client";

/** The six steps every project goes through, shown on every project screen. */
export type StepId = "upload" | "analyze" | "edit" | "review" | "generate" | "compare";
export type StepRoute = "new" | "project" | "review" | "job" | "result";
export type StepStatus = "done" | "current" | "available" | "locked";

export const STEPS: { id: StepId; n: number; label: string }[] = [
  { id: "upload", n: 1, label: "Enviar" },
  { id: "analyze", n: 2, label: "Analisar" },
  { id: "edit", n: 3, label: "Editar" },
  { id: "review", n: 4, label: "Revisar" },
  { id: "generate", n: 5, label: "Gerar" },
  { id: "compare", n: 6, label: "Comparar" },
];

const RUNNING = new Set(["QUEUED", "PREPARING", "ANALYZING", "GENERATING", "QA", "REPAIRING", "ASSEMBLING"]);

type StepProject = Pick<Project, "id" | "sourceVideo" | "analysis" | "activeJob" | "editCount" | "latestOutputId">;

function uploadDone(p: StepProject): boolean {
  const status = p.sourceVideo?.status;
  return !!status && status !== "PENDING_UPLOAD" && status !== "REJECTED";
}

function analysisDone(p: StepProject): boolean {
  return p.analysis?.status === "COMPLETED";
}

export function analysisRunning(p: StepProject): boolean {
  const job = p.activeJob;
  return !!job && (job.kind === "ANALYSIS" || job.kind === "INGEST") && RUNNING.has(job.status);
}

function runningGeneration(p: StepProject) {
  const job = p.activeJob;
  return job && job.kind === "GENERATION" && RUNNING.has(job.status) ? job : null;
}

/** Which step a screen shows. The project screen is upload, analysis or editor depending on state. */
export function currentStep(route: StepRoute, project?: StepProject | null): StepId {
  if (route === "new") return "upload";
  if (route === "review") return "review";
  if (route === "job") return "generate";
  if (route === "result") return "compare";
  if (!project || !uploadDone(project)) return "upload";
  if (analysisDone(project) && !analysisRunning(project)) return "edit";
  return "analyze";
}

/** Where a step's pill links to, or null when it cannot be opened yet (or no longer needs to be). */
export function stepHref(step: StepId, project?: StepProject | null): string | null {
  if (!project) return null;
  const base = `/projects/${project.id}`;
  switch (step) {
    case "edit":
      return analysisDone(project) ? base : null;
    case "review":
      return analysisDone(project) && project.editCount > 0 ? `${base}/review` : null;
    case "generate": {
      const job = runningGeneration(project);
      return job ? `${base}/jobs/${job.id}` : null;
    }
    case "compare":
      return project.latestOutputId ? `${base}/result` : null;
    default:
      return null;
  }
}

export function stepStatus(step: StepId, current: StepId, project?: StepProject | null): StepStatus {
  if (step === current) return "current";
  if (!project) return "locked";
  const done: Record<StepId, boolean> = {
    upload: uploadDone(project),
    analyze: analysisDone(project),
    edit: project.editCount > 0,
    review: !!project.latestOutputId || !!runningGeneration(project),
    generate: !!project.latestOutputId,
    compare: false,
  };
  if (done[step]) return "done";
  return stepHref(step, project) ? "available" : "locked";
}

export type StepState = "normal" | "running" | "failed" | "cancelled" | "rejected" | "blocked";

/** One plain-language line telling the user what to do now. */
export function stepGuidance(
  step: StepId,
  { state = "normal", editCount = 0, mock = false }: { state?: StepState; editCount?: number; mock?: boolean } = {},
): string {
  switch (step) {
    case "upload":
      if (state === "running")
        return "Enviando seu vídeo… Não feche esta aba. Se a conexão cair, clique em Enviar de novo: continuamos de onde parou.";
      if (state === "rejected") return "Não deu para usar este arquivo. Escolha outro vídeo (MP4, MOV, WebM ou MKV).";
      return "Escolha o vídeo e confirme que você tem direito de usá-lo. Sem vídeo agora? Use o exemplo.";
    case "analyze":
      if (state === "failed")
        return "A análise não terminou. Clique em “Analisar de novo”. Se acontecer outra vez, tente outro vídeo.";
      if (state === "cancelled") return "Você cancelou a análise. Clique em “Analisar de novo” quando quiser continuar.";
      return "Estamos separando seu vídeo em cenas, personagens, roupas, objetos e cenário. Leva cerca de 1 minuto — pode esperar aqui.";
    case "edit":
      if (editCount === 0)
        return "Clique em um elemento à esquerda (ou numa caixa sobre o vídeo) e escolha como ele deve mudar.";
      return `Você tem ${editCount} ${editCount === 1 ? "alteração" : "alterações"}. Continue mudando ou clique em “Revisar e gerar”.`;
    case "review":
      if (state === "blocked")
        return "Uma alteração entra em conflito com o que você pediu para manter. Volte para Editar e ajuste antes de gerar.";
      return `Confira o que muda e quanto custa. Nada é gerado até você clicar em “Gerar”.${mock ? " Valores simulados — nada é cobrado." : ""}`;
    case "generate":
      if (state === "failed") return "A geração não terminou. Volte para Revisar e tente de novo.";
      if (state === "cancelled") return "Você cancelou a geração. Volte para Revisar quando quiser tentar de novo.";
      return "Gerando cena por cena e conferindo cada uma. Pode sair desta página: o trabalho continua.";
    case "compare":
      return mock
        ? "Compare o antes e o depois. No modo demonstração, as mudanças aparecem como marcações coloridas sobre o vídeo original."
        : "Compare o antes e o depois. Gostou? Gere a versão final. Quer ajustar? Volte para Editar.";
  }
}
