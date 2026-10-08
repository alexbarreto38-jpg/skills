"use client";

import type { QualityMode } from "@videodna/api-client";
import { AlertTriangle, ArrowLeft, Ban, Clapperboard, Cpu, Film, Layers, Sparkles, Wallet } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { Badge, Button, EmptyState, Segmented, Spinner, cx, impactTone } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { formatDuration, formatMoney, formatTime } from "@/lib/format";
import { DEPENDENCY, IMPACT, QUALITY_MODE, STRATEGY, label } from "@/lib/labels";
import { useCreatePlan, useGenerate, useProject } from "@/lib/queries";

interface PlanShot {
  shotKey: string;
  startTime: number;
  endTime: number;
  strategy: string;
  estimatedCost: number;
  qaProvider?: string | null;
  edits: { description: string; changeKind: string; entityLabel: string }[];
  steps: { strategy: string; provider: string; model?: string; estimatedCost: number; chunks: number; routing?: { reasons?: string[] } }[];
  dependencies: { type: string; description: string; futureFeature?: boolean }[];
  referencePacks: string[];
}
interface PlanDoc {
  summary: { totalShots: number; affectedShots: number; passthroughShots: number; generations: number; editCount: number };
  shots: PlanShot[];
  referencePacks: { id: string; label: string; description: string; shotKeys: string[] }[];
  impacts: { operationId: string; level: string; reasons: string[]; entityId?: string | null }[];
  warnings: { code: string; message: string; blocking: boolean }[];
  estimatedCost: number;
  estimatedCostWithRepairs: number;
  currency: string;
  resolutionLabel: string;
  maxRetries: number;
  providers: string[];
  expectedDurationSec: number;
  operations: { id: string; op: string; entityId?: string | null }[];
}

const STRATEGY_TONE: Record<string, "neutral" | "ok" | "cyan" | "warn" | "accent" | "bad"> = {
  PASSTHROUGH: "neutral",
  ATTRIBUTE_EDIT: "ok",
  LOCALIZED_EDIT: "cyan",
  BACKGROUND_REPLACEMENT: "warn",
  SHOT_RECONSTRUCTION: "accent",
  FULL_REGENERATION: "bad",
};

function Stat({ icon, label: text, value, hint }: { icon: React.ReactNode; label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="panel p-4">
      <p className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-faint">
        {icon} {text}
      </p>
      <p className="mt-1.5 text-xl font-semibold tracking-tight">{value}</p>
      {hint && <p className="mt-0.5 text-xs text-muted">{hint}</p>}
    </div>
  );
}

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: project } = useProject(id);
  const createPlan = useCreatePlan(id);
  const generate = useGenerate(id);
  const [mode, setMode] = useState<QualityMode | null>(null);
  const [render, setRender] = useState<"preview" | "final">("preview");
  const quality = mode ?? project?.settings.qualityMode ?? "BALANCED";

  const { mutate: makePlan } = createPlan;
  useEffect(() => {
    if (project) makePlan({ qualityMode: quality, renderKind: render });
  }, [project?.id, project?.editCount, quality, render, makePlan]); // eslint-disable-line react-hooks/exhaustive-deps

  const planOut = createPlan.data;
  const plan = planOut?.plan as unknown as PlanDoc | undefined;
  const idempotencyKey = useMemo(() => (planOut?.id ? `ui:${planOut.id}` : ""), [planOut?.id]);

  function start() {
    if (!planOut?.id) return;
    generate.mutate(
      { planId: planOut.id, idempotencyKey },
      {
        onSuccess: (job) => router.push(`/projects/${id}/jobs/${job.id}`),
        onError: (e) => toast.error("Não foi possível iniciar", errorMessage(e)),
      },
    );
  }

  const blocking = plan?.warnings.filter((w) => w.blocking) ?? [];
  const notes = plan?.warnings.filter((w) => !w.blocking) ?? [];

  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <Link href={`/projects/${id}`} className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted hover:text-fg">
          <ArrowLeft className="size-3.5" /> Voltar ao editor
        </Link>
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Revisar alterações</h1>
            <p className="mt-1 text-sm text-muted">
              Nada é gerado sem plano: veja estratégia, provider e custo de cada shot antes de confirmar.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Segmented
              value={quality}
              onChange={(v) => setMode(v)}
              options={(["ECONOMY", "BALANCED", "MAX"] as const).map((m) => ({ value: m, label: QUALITY_MODE[m].label, hint: QUALITY_MODE[m].hint }))}
            />
            <Segmented
              value={render}
              onChange={setRender}
              options={[
                { value: "preview", label: "Preview 720p" },
                { value: "final", label: "Final 1080p" },
              ]}
            />
          </div>
        </div>

        {!plan ? (
          createPlan.isError ? (
            <EmptyState title="Não foi possível montar o plano">{errorMessage(createPlan.error)}</EmptyState>
          ) : (
            <div className="flex items-center justify-center gap-2 py-24 text-sm text-muted">
              <Spinner /> Montando o Generation Plan…
            </div>
          )
        ) : (
          <div className={cx("space-y-6 transition-opacity", createPlan.isPending && "opacity-50")}>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <Stat
                icon={<Wallet className="size-3.5" />}
                label="Estimativa"
                value={formatMoney(plan.estimatedCost, plan.currency)}
                hint={`até ${formatMoney(plan.estimatedCostWithRepairs, plan.currency)} com ${plan.maxRetries} reparo(s)`}
              />
              <Stat
                icon={<Clapperboard className="size-3.5" />}
                label="Shots afetados"
                value={`${plan.summary.affectedShots} de ${plan.summary.totalShots}`}
                hint={`${plan.summary.passthroughShots} copiado(s) sem custo`}
              />
              <Stat
                icon={<Layers className="size-3.5" />}
                label="Gerações"
                value={plan.summary.generations}
                hint={`${plan.summary.editCount} alteração(ões) · ${plan.resolutionLabel}`}
              />
              <Stat
                icon={<Cpu className="size-3.5" />}
                label="Modelos prováveis"
                value={<span className="text-base">{plan.providers.filter((p) => !p.startsWith("ffmpeg")).length}</span>}
                hint={`~${formatDuration(plan.expectedDurationSec)} de processamento`}
              />
            </div>

            {blocking.length > 0 && (
              <div className="space-y-1.5 rounded-xl border border-bad/40 bg-bad/10 p-4">
                {blocking.map((w) => (
                  <p key={w.code + w.message} className="flex gap-2 text-sm text-bad">
                    <Ban className="mt-0.5 size-4 shrink-0" /> {w.message}
                  </p>
                ))}
                <p className="text-xs text-muted">Resolva os conflitos no editor (ou desligue o lock correspondente) para gerar.</p>
              </div>
            )}

            <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
              <section className="panel overflow-hidden">
                <div className="border-b border-line px-4 py-3 text-sm font-medium">Plano por shot</div>
                <ul className="divide-y divide-line">
                  {plan.shots.map((s) => (
                    <li key={s.shotKey} className="space-y-2 px-4 py-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs text-faint">{s.shotKey}</span>
                        <span className="font-mono text-[11px] text-faint">
                          {formatTime(s.startTime)}–{formatTime(s.endTime)}
                        </span>
                        {s.steps.length ? (
                          s.steps.map((st, i) => (
                            <Badge key={i} tone={STRATEGY_TONE[st.strategy]}>
                              {label(STRATEGY, st.strategy)}
                            </Badge>
                          ))
                        ) : (
                          <Badge>{label(STRATEGY, "PASSTHROUGH")}</Badge>
                        )}
                        <span className="flex-1" />
                        <span className="text-sm font-medium">{s.estimatedCost ? formatMoney(s.estimatedCost, plan.currency) : "—"}</span>
                      </div>
                      {s.edits.length > 0 && (
                        <p className="text-xs text-fg/90">{s.edits.map((e) => e.description).join(" · ")}</p>
                      )}
                      {s.steps.length > 0 && (
                        <p className="text-[11px] text-muted">
                          {s.steps.map((st) => `${st.provider}${st.model ? ` (${st.model})` : ""}${st.chunks > 1 ? ` ×${st.chunks}` : ""}`).join(" → ")}
                          {s.qaProvider && ` · QA: ${s.qaProvider}`}
                          {s.referencePacks.length > 0 && ` · ${s.referencePacks.length} reference pack(s)`}
                        </p>
                      )}
                      {s.dependencies.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {[...new Map(s.dependencies.map((d) => [d.type, d])).values()].map((d) => (
                            <span
                              key={d.type}
                              title={d.description}
                              className={cx("rounded-md px-1.5 py-0.5 text-[10px]", d.futureFeature ? "bg-panel-3 text-faint" : "bg-cyan/10 text-cyan")}
                            >
                              {label(DEPENDENCY, d.type)}
                            </span>
                          ))}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              </section>

              <aside className="space-y-4">
                <section className="panel p-4">
                  <h3 className="mb-3 text-sm font-medium">Alterações</h3>
                  <ul className="space-y-2">
                    {plan.impacts
                      .filter((i) => i.level !== "NONE")
                      .map((i) => (
                        <li key={i.operationId} className="flex items-start gap-2 text-xs">
                          <Badge tone={impactTone(i.level)}>{label(IMPACT, i.level).replace("Impacto ", "")}</Badge>
                          <span className="text-muted">{i.reasons[0]}</span>
                        </li>
                      ))}
                  </ul>
                </section>
                {plan.referencePacks.length > 0 && (
                  <section className="panel p-4">
                    <h3 className="mb-3 text-sm font-medium">Continuidade</h3>
                    <ul className="space-y-2">
                      {plan.referencePacks.map((p) => (
                        <li key={p.id} className="text-xs">
                          <p className="text-fg/90">{p.label}</p>
                          <p className="text-faint">{p.shotKeys.length} shot(s) · {p.description}</p>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
                {notes.length > 0 && (
                  <section className="panel space-y-2 p-4">
                    {notes.map((w) => (
                      <p key={w.code + w.message} className="flex gap-2 text-xs text-muted">
                        <AlertTriangle className="mt-0.5 size-3.5 shrink-0 text-warn" /> {w.message}
                      </p>
                    ))}
                  </section>
                )}
                <Button
                  variant="primary"
                  size="lg"
                  className="w-full"
                  icon={<Sparkles className="size-4" />}
                  disabled={!!blocking.length || createPlan.isPending || !planOut?.id}
                  loading={generate.isPending}
                  onClick={start}
                >
                  Gerar {render === "final" ? "versão final" : "preview"} · {formatMoney(plan.estimatedCost, plan.currency)}
                </Button>
                <p className="flex items-center gap-1.5 text-[11px] text-faint">
                  <Film className="size-3" /> O áudio original e a duração de cada shot são preservados conforme os locks.
                </p>
              </aside>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
