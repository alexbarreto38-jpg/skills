"use client";

import type { Project } from "@videodna/api-client";
import { Check } from "lucide-react";
import Link from "next/link";

import { cx } from "@/components/ui/primitives";
import { useAppConfig } from "@/lib/queries";
import {
  STEPS,
  type StepRoute,
  type StepState,
  currentStep,
  stepGuidance,
  stepHref,
  stepStatus,
} from "@/lib/steps";

/**
 * "Where am I and what do I do now": the six steps of a project, with the
 * current one highlighted and a one-line instruction under it.
 */
export function ProjectSteps({
  project,
  route,
  state = "normal",
  compact = false,
  className,
}: {
  project?: Project | null;
  route: StepRoute;
  state?: StepState;
  /** Pills only (no instruction line), for the editor's top bar. */
  compact?: boolean;
  className?: string;
}) {
  const { data: config } = useAppConfig();
  const current = currentStep(route, project);
  const guidance = stepGuidance(current, {
    state,
    editCount: project?.editCount ?? 0,
    mock: !!config?.mockMode,
  });

  return (
    <div className={cx(compact ? "" : "space-y-2", className)}>
      <nav aria-label="Etapas do projeto">
        <ol className="flex flex-wrap items-center gap-1">
          {STEPS.map((step, i) => {
            const status = stepStatus(step.id, current, project);
            const href = status === "current" ? null : stepHref(step.id, project);
            const pill = (
              <span
                aria-current={status === "current" ? "step" : undefined}
                className={cx(
                  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors",
                  status === "current" && "border-accent bg-accent/15 font-medium text-fg",
                  status === "done" && "border-line text-muted",
                  status === "available" && "border-line text-muted hover:border-line-strong hover:text-fg",
                  status === "locked" && "border-transparent text-faint",
                )}
              >
                <span
                  className={cx(
                    "flex size-4 items-center justify-center rounded-full text-[10px]",
                    status === "current" ? "bg-accent text-white" : status === "done" ? "bg-ok/20 text-ok" : "bg-panel-3",
                  )}
                >
                  {status === "done" ? <Check className="size-3" /> : step.n}
                </span>
                <span className={cx(compact && status !== "current" && "hidden xl:inline")}>{step.label}</span>
              </span>
            );
            return (
              <li key={step.id} className="flex items-center gap-1">
                {href ? (
                  <Link href={href} title={`Ir para: ${step.label}`}>
                    {pill}
                  </Link>
                ) : (
                  pill
                )}
                {i < STEPS.length - 1 && <span aria-hidden className="h-px w-2 bg-line" />}
              </li>
            );
          })}
        </ol>
      </nav>
      {!compact && <p className="text-sm text-muted">{guidance}</p>}
    </div>
  );
}
