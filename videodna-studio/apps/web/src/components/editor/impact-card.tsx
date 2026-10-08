"use client";

import type { ImpactReport } from "@videodna/api-client";
import { AlertTriangle, Ban, Link2, Sparkles } from "lucide-react";

import { Badge, cx, impactTone } from "@/components/ui/primitives";
import { DEPENDENCY, IMPACT, label } from "@/lib/labels";

/** Impact analysis shown discreetly before applying an edit (spec §77). */
export function ImpactCard({ impact, compact }: { impact: ImpactReport; compact?: boolean }) {
  const deps = impact.dependencies ?? [];
  const warnings = impact.warnings ?? [];
  return (
    <div className="space-y-2 rounded-xl border border-line bg-panel-2 p-3">
      <div className="flex items-center justify-between gap-2">
        <Badge tone={impactTone(impact.level)}>{label(IMPACT, impact.level)}</Badge>
        <span className="text-[11px] text-muted">
          {impact.affectedShotIds?.length ?? 0} shot(s) · {impact.affectedEntityIds?.length ?? 0} elemento(s)
        </span>
      </div>
      {warnings.map((w) => (
        <p
          key={w.code + w.message}
          className={cx(
            "flex gap-2 rounded-lg px-2 py-1.5 text-xs",
            w.blocking ? "bg-bad/10 text-bad" : "bg-warn/10 text-warn",
          )}
        >
          {w.blocking ? <Ban className="mt-0.5 size-3.5 shrink-0" /> : <AlertTriangle className="mt-0.5 size-3.5 shrink-0" />}
          {w.message}
        </p>
      ))}
      {!compact && deps.length > 0 && (
        <ul className="space-y-1">
          {deps.map((d, i) => (
            <li key={`${d.type}-${i}`} className="flex gap-2 text-xs text-muted">
              {d.futureFeature ? (
                <Sparkles className="mt-0.5 size-3.5 shrink-0 text-faint" />
              ) : (
                <Link2 className="mt-0.5 size-3.5 shrink-0 text-cyan" />
              )}
              <span>
                <span className="text-fg/90">{label(DEPENDENCY, d.type)}:</span> {d.description}
                {d.futureFeature && <span className="text-faint"> (futuro)</span>}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
