"use client";

import { ChevronRight, Wrench } from "lucide-react";

import { Money } from "@/components/ui/money";
import { Badge } from "@/components/ui/primitives";
import { formatTime } from "@/lib/format";

import { DEPENDENCY_PLAIN, type PlanDoc, STRATEGY_PLAIN, plural, sceneName } from "./plan-text";

const STRATEGY_TONE: Record<string, "neutral" | "ok" | "cyan" | "warn" | "accent" | "bad"> = {
  PASSTHROUGH: "neutral",
  ATTRIBUTE_EDIT: "ok",
  LOCALIZED_EDIT: "cyan",
  BACKGROUND_REPLACEMENT: "warn",
  SHOT_RECONSTRUCTION: "accent",
  FULL_REGENERATION: "bad",
};

/**
 * The per-scene technical plan, closed by default. This is the only place
 * that names AI services, models and reference packs: useful to check, never
 * needed to decide.
 */
export function PlanDetails({ plan, technical }: { plan: PlanDoc; technical: string[] }) {
  const services = plan.providers.filter((p) => !p.startsWith("ffmpeg"));
  return (
    <details className="group panel overflow-hidden">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-3 text-sm font-medium text-muted hover:text-fg [&::-webkit-details-marker]:hidden">
        <Wrench className="size-4" />
        <span className="flex-1">Ver detalhes por cena (técnico)</span>
        <ChevronRight className="size-4 transition-transform group-open:rotate-90" />
      </summary>
      <div className="space-y-2 border-t border-line px-4 py-3 text-xs leading-relaxed text-muted">
        <p>Como cada cena vai ser feita. Você não precisa mexer em nada aqui.</p>
        <p>
          {plural(plan.summary.generations, "etapa de IA", "etapas de IA")}
          {plan.maxRetries > 0 && ` · até ${plural(plan.maxRetries, "nova tentativa", "novas tentativas")} se algo sair errado`}
          {services.length > 0 && ` · serviços: ${services.join(", ")}`}
        </p>
        {technical.length > 0 && (
          <ul className="list-disc space-y-0.5 pl-4">
            {technical.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        )}
      </div>
      <ul className="divide-y divide-line border-t border-line">
        {plan.shots.map((s) => {
          const strategy = s.steps.length ? s.steps.map((st) => st.strategy) : ["PASSTHROUGH"];
          const cautions = [...new Map(s.dependencies.map((d) => [d.type, d])).values()];
          return (
            <li key={s.shotKey} className="space-y-1.5 px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium">{sceneName(s.shotKey, s.index)}</span>
                <span className="font-mono text-[11px] text-faint">
                  {formatTime(s.startTime)}–{formatTime(s.endTime)}
                </span>
                {strategy.map((st, i) => (
                  <Badge key={i} tone={STRATEGY_TONE[st]}>
                    {STRATEGY_PLAIN[st] ?? "Mudança"}
                  </Badge>
                ))}
                <span className="flex-1" />
                {s.estimatedCost ? (
                  <Money className="text-sm font-medium" value={s.estimatedCost} currency={plan.currency} />
                ) : (
                  <span className="text-xs text-faint">sem custo</span>
                )}
              </div>
              {s.edits.length > 0 && <p className="text-xs text-fg/90">{s.edits.map((e) => e.description).join(" · ")}</p>}
              {s.steps.length > 0 && (
                <p className="text-[11px] text-muted">
                  Serviço de IA:{" "}
                  {s.steps
                    .map((st) => `${st.provider}${st.model ? ` (${st.model})` : ""}${st.chunks > 1 ? ` em ${st.chunks} partes` : ""}`)
                    .join(" → ")}
                  {s.qaProvider && ` · conferência: ${s.qaProvider}`}
                  {s.referencePacks.length > 0 &&
                    ` · ${plural(s.referencePacks.length, "referência", "referências")} de continuidade`}
                </p>
              )}
              {cautions.length > 0 && (
                <div className="flex flex-wrap items-center gap-1">
                  <span className="text-[11px] text-faint">Cuidados:</span>
                  {cautions.map((d) => (
                    <span
                      key={d.type}
                      title={d.description}
                      className={d.futureFeature ? "rounded-md bg-panel-3 px-1.5 py-0.5 text-[10px] text-faint" : "rounded-md bg-cyan/10 px-1.5 py-0.5 text-[10px] text-cyan"}
                    >
                      {DEPENDENCY_PLAIN[d.type] ?? d.description}
                    </span>
                  ))}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}
