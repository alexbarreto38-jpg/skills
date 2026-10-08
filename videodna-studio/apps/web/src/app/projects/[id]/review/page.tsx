"use client";

import type { QualityMode } from "@videodna/api-client";
import { ArrowLeft, Clapperboard, Clock, FlaskConical, Sparkles, Wallet } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { ProjectSteps } from "@/components/project/project-steps";
import { PlanDetails } from "@/components/review/plan-details";
import {
  BackToEditor,
  BlockingNotices,
  ChangeSummary,
  ChoiceGroup,
  Notes,
  NothingToGenerate,
  Stat,
} from "@/components/review/plan-sections";
import {
  type PlanDoc,
  continuityText,
  durationLabel,
  groupWarnings,
  keptText,
  summarizeChanges,
} from "@/components/review/plan-text";
import { Money, useDemoMode } from "@/components/ui/money";
import { Button, Spinner, cx } from "@/components/ui/primitives";
import { LoadError } from "@/components/ui/server-offline";
import { toast } from "@/components/ui/toast";
import { ApiError, errorMessage } from "@/lib/api";
import { useEditor } from "@/lib/editor-store";
import { QUALITY_MODE } from "@/lib/labels";
import { useCreatePlan, useGenerate, useProject } from "@/lib/queries";

type RenderKind = "preview" | "final";
type PlanOut = NonNullable<ReturnType<typeof useCreatePlan>["data"]>;

const QUALITY_OPTIONS = (["ECONOMY", "BALANCED", "MAX"] as const).map((m) => ({
  value: m,
  label: QUALITY_MODE[m].label,
  hint: QUALITY_MODE[m].hint,
}));
const RENDER_OPTIONS = [
  { value: "preview", label: "Rascunho" },
  { value: "final", label: "Versão final" },
] as const;

/** "Sai em 720p", saying why when the final version cannot be sharper than the original. */
function resolutionHelp(render: RenderKind, resolution: string): string {
  const lines = parseInt(resolution, 10);
  if (render === "final" && lines < 1080)
    return ` Seu vídeo original é ${resolution}, então a versão final também sai em ${resolution}.`;
  return ` ${render === "final" ? "A versão final" : "O rascunho"} sai em ${resolution}.`;
}

function Centered({ children }: { children: ReactNode }) {
  return <div className="flex items-center justify-center gap-2 py-24 text-sm text-muted">{children}</div>;
}

/** Tela 5: what will change, what it costs and how long it takes — then one button to generate. */
export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const demo = useDemoMode();
  const { data: project, isLoading, error, refetch } = useProject(id);
  const createPlan = useCreatePlan(id);
  const generate = useGenerate(id);
  const [mode, setMode] = useState<QualityMode | null>(null);
  const [render, setRender] = useState<RenderKind>("preview");
  // Kept across re-plans so changing an option dims the numbers instead of
  // flashing the whole page back to a spinner (the mutation clears its data
  // while the next request is pending).
  const [planOut, setPlanOut] = useState<PlanOut | null>(null);
  const quality = mode ?? project?.settings.qualityMode ?? "BALANCED";
  const projectId = project?.id;
  const editCount = project?.editCount ?? 0;

  const { mutate: makePlan } = createPlan;
  function replan() {
    makePlan(
      { qualityMode: quality, renderKind: render },
      // A failed re-plan must not leave the previous options' plan behind a button that would run it.
      { onSuccess: setPlanOut, onError: () => setPlanOut(null) },
    );
  }
  useEffect(() => {
    if (projectId && editCount > 0)
      makePlan({ qualityMode: quality, renderKind: render }, { onSuccess: setPlanOut, onError: () => setPlanOut(null) });
  }, [projectId, editCount, quality, render, makePlan]);

  const plan = planOut?.plan as unknown as PlanDoc | undefined;
  const groups = useMemo(() => (plan ? groupWarnings(plan.warnings) : null), [plan]);
  const changes = useMemo(() => (plan ? summarizeChanges(plan.shots) : []), [plan]);
  const editorHref = `/projects/${id}`;

  function openInEditor(entityKey: string | null) {
    // The editor opens on the current selection, so the problem element is
    // already selected when it mounts; the query parameter carries it too.
    if (entityKey) useEditor.getState().select(entityKey);
    router.push(entityKey ? `${editorHref}?select=${encodeURIComponent(entityKey)}` : editorHref);
  }

  function start() {
    if (!planOut?.id) return;
    generate.mutate(
      { planId: planOut.id, idempotencyKey: `ui:${planOut.id}` },
      {
        onSuccess: (job) => router.push(`/projects/${id}/jobs/${job.id}`),
        onError: (e) => {
          // The changes moved on (another tab, or this plan already ran): recompute and let the user confirm again.
          if (e instanceof ApiError && (e.code === "PLAN_STALE" || e.code === "CONFLICT")) {
            toast.info(
              "Os valores foram atualizados",
              "Suas mudanças mudaram desde que esta tela abriu. Confira de novo e clique para gerar.",
            );
            replan();
            return;
          }
          toast.error("Não foi possível começar a gerar", errorMessage(e));
        },
      },
    );
  }

  let body: ReactNode;
  let stepsState: "normal" | "blocked" = "normal";
  let guidance = true;
  if (isLoading) {
    body = (
      <Centered>
        <Spinner /> Abrindo o projeto…
      </Centered>
    );
  } else if (error || !project) {
    guidance = false;
    body = <LoadError error={error} onRetry={() => refetch()} title="Projeto não encontrado" />;
  } else if (editCount === 0) {
    guidance = false;
    body = <NothingToGenerate reason="no-edits" editorHref={editorHref} />;
  } else if (!plan || !groups) {
    if (createPlan.isError) {
      guidance = false;
      body = (
        <div className="panel pb-6">
          <LoadError error={createPlan.error} onRetry={replan} title="Não deu para calcular o que vai mudar" />
          <div className="flex justify-center">
            <BackToEditor href={editorHref} />
          </div>
        </div>
      );
    } else {
      body = (
        <Centered>
          <Spinner /> Calculando o que muda, quanto custa e quanto demora…
        </Centered>
      );
    }
  } else if (groups.nothing) {
    guidance = false;
    body = <NothingToGenerate reason={groups.nothing} editorHref={editorHref} />;
  } else {
    if (groups.lockConflict) stepsState = "blocked";
    const blocked = groups.blocking.length > 0;
    const pending = createPlan.isPending;
    const { summary } = plan;
    const others = summary.totalShots - summary.affectedShots;
    body = (
      <div className="space-y-6">
        {blocked && <BlockingNotices notices={groups.blocking} onFix={openInEditor} />}

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-start">
          <div className={cx("space-y-4 transition-opacity", pending && "opacity-50")} aria-busy={pending}>
            <ChangeSummary
              changes={changes}
              totalScenes={summary.totalShots}
              kept={keptText(plan.locks)}
              continuity={continuityText(plan.referencePacks)}
            />
            <div className="grid gap-3 sm:grid-cols-3">
              <Stat
                icon={<Wallet className="size-3.5" />}
                label="Custo estimado"
                value={<Money value={plan.estimatedCost} currency={plan.currency} />}
                hint={
                  plan.estimatedCostWithRepairs > plan.estimatedCost && (
                    <>
                      pode chegar a <Money value={plan.estimatedCostWithRepairs} currency={plan.currency} /> se for preciso
                      refazer trechos
                    </>
                  )
                }
              />
              <Stat
                icon={<Clapperboard className="size-3.5" />}
                label="Cenas que mudam"
                value={`${summary.affectedShots} de ${summary.totalShots}`}
                hint={
                  others === 0
                    ? "todas as cenas do vídeo"
                    : others === 1
                      ? "a outra fica igual, sem custo"
                      : `as outras ${others} ficam iguais, sem custo`
                }
              />
              <Stat
                icon={<Clock className="size-3.5" />}
                label="Tempo estimado"
                value={durationLabel(plan.expectedDurationSec)}
                hint="pode sair da página enquanto gera"
              />
            </div>
            {groups.notes.length > 0 && <Notes notices={groups.notes} onFix={openInEditor} />}
          </div>

          <aside className="panel space-y-5 p-4 lg:sticky lg:top-6">
            <h2 className="text-base font-semibold tracking-tight">Escolha como gerar</h2>
            <ChoiceGroup
              name="quality"
              legend="Qualidade"
              value={quality}
              onChange={setMode}
              options={QUALITY_OPTIONS}
              help="Econômico custa menos; Qualidade máxima fica melhor, mas custa mais. Na dúvida, use Equilibrado."
            />
            <ChoiceGroup
              name="render"
              legend="Tipo de vídeo"
              value={render}
              onChange={setRender}
              options={RENDER_OPTIONS}
              help={
                "Comece pelo rascunho para conferir; gere a versão final quando gostar do resultado." +
                (pending ? "" : resolutionHelp(render, plan.resolutionLabel))
              }
            />
            <div className="space-y-2 border-t border-line pt-4">
              <Button
                variant="primary"
                size="lg"
                className="w-full"
                icon={<Sparkles className="size-4" />}
                disabled={blocked || pending || !planOut?.id}
                loading={generate.isPending}
                onClick={start}
              >
                {render === "final" ? "Gerar versão final" : "Gerar rascunho"}
              </Button>
              <p className="flex items-center justify-center gap-1.5 text-center text-xs text-muted">
                {pending ? (
                  <>
                    <Spinner className="size-3" /> Atualizando os valores…
                  </>
                ) : (
                  <span>
                    Custo estimado: <Money className="font-medium text-fg" value={plan.estimatedCost} currency={plan.currency} />
                  </span>
                )}
              </p>
              {blocked && <p className="text-center text-xs text-bad">Resolva o aviso no topo da página para poder gerar.</p>}
              {demo && (
                <p className="flex gap-1.5 text-[11px] leading-relaxed text-faint">
                  <FlaskConical className="mt-0.5 size-3 shrink-0 text-warn" />
                  Modo demonstração: o vídeo gerado mostra marcações coloridas onde cada mudança seria feita.
                </p>
              )}
            </div>
          </aside>
        </div>

        <div className={cx("transition-opacity", pending && "opacity-50")}>
          <PlanDetails plan={plan} technical={groups.technical} />
        </div>
      </div>
    );
  }

  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <Link href={editorHref} className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted hover:text-fg">
          <ArrowLeft className="size-3.5" /> Voltar ao editor
        </Link>
        <h1 className="mb-4 text-2xl font-semibold tracking-tight">Revisar e gerar</h1>
        <ProjectSteps project={project} route="review" state={stepsState} compact={!guidance} className="mb-6" />
        {body}
      </main>
    </div>
  );
}
