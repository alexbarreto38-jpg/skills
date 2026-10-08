"use client";

import type { JobEvent } from "@videodna/api-client";
import { Check, CircleAlert, Loader2, Wrench } from "lucide-react";
import { useEffect, useRef } from "react";

import { Badge, Button, Progress, cx, statusTone } from "@/components/ui/primitives";
import { JOB_STATUS, label } from "@/lib/labels";
import { useCancelJob, useJobStream } from "@/lib/queries";

export function JobProgress({
  jobId,
  stages,
  title,
  onFinished,
}: {
  jobId: string;
  stages: { id: string; label: string }[];
  title: string;
  onFinished?: (status: string) => void;
}) {
  const { job, events } = useJobStream(jobId);
  const cancel = useCancelJob();
  const finished = useRef(false);
  const log = useRef<HTMLDivElement>(null);

  const status = job?.status ?? "QUEUED";
  const terminal = ["COMPLETED", "FAILED", "CANCELLED"].includes(status);
  useEffect(() => {
    if (terminal && !finished.current) {
      finished.current = true;
      onFinished?.(status);
    }
  }, [terminal, status, onFinished]);
  useEffect(() => {
    log.current?.scrollTo({ top: log.current.scrollHeight, behavior: "smooth" });
  }, [events.length]);

  const seen = new Set(events.map((e) => e.stage).filter(Boolean));
  const currentStage = job?.stage;
  const currentIndex = stages.findIndex((s) => s.id === currentStage);

  return (
    <div className="panel overflow-hidden">
      <div className="border-b border-line p-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
          <Badge tone={statusTone(status)}>{label(JOB_STATUS, status)}</Badge>
        </div>
        <Progress value={job?.progress ?? 0} tone={status === "FAILED" ? "bad" : status === "COMPLETED" ? "ok" : "accent"} />
        <div className="mt-2 flex items-center justify-between gap-3 text-xs">
          <span className="truncate text-muted">{job?.message}</span>
          <span className="font-mono text-faint">{Math.round(job?.progress ?? 0)}%</span>
        </div>
        {status === "FAILED" && job?.errorMessage && (
          <p className="mt-3 flex items-center gap-2 rounded-lg bg-bad/10 px-3 py-2 text-sm text-bad">
            <CircleAlert className="size-4" /> {job.errorMessage}
          </p>
        )}
      </div>
      <div className="grid gap-0 md:grid-cols-[260px_1fr]">
        <ol className="space-y-1 border-b border-line p-4 md:border-b-0 md:border-r">
          {stages.map((stage, i) => {
            const done = terminal ? status === "COMPLETED" || seen.has(stage.id) : i < currentIndex || (seen.has(stage.id) && stage.id !== currentStage);
            const active = !terminal && stage.id === currentStage;
            return (
              <li key={stage.id} className="flex items-center gap-2.5 py-1 text-sm">
                <span
                  className={cx(
                    "flex size-5 items-center justify-center rounded-full border",
                    done ? "border-ok bg-ok/15 text-ok" : active ? "border-accent text-accent" : "border-line-strong text-faint",
                  )}
                >
                  {done ? <Check className="size-3" /> : active ? <Loader2 className="size-3 animate-spin" /> : null}
                </span>
                <span className={cx(active ? "text-fg" : done ? "text-muted" : "text-faint")}>{stage.label}</span>
              </li>
            );
          })}
        </ol>
        <div ref={log} className="max-h-72 overflow-y-auto p-4 font-mono text-[12px] leading-6">
          {events.length === 0 && <p className="text-faint">Conectando ao progresso em tempo real…</p>}
          {events.map((e: JobEvent) => (
            <div key={e.seq} className={cx("flex gap-3", e.level === "warning" ? "text-warn" : e.level === "error" ? "text-bad" : "text-muted")}>
              <span className="w-10 shrink-0 text-right text-faint">{Math.round(e.progress)}%</span>
              {e.stage === "repair" && <Wrench className="mt-1.5 size-3 shrink-0 text-warn" />}
              <span className="min-w-0">{e.message}</span>
            </div>
          ))}
        </div>
      </div>
      {!terminal && (
        <div className="flex items-center justify-between border-t border-line px-5 py-3">
          <span className="font-mono text-[11px] text-faint">job {jobId.slice(0, 8)}</span>
          <Button size="sm" variant="ghost" loading={cancel.isPending} onClick={() => cancel.mutate(jobId)}>
            Cancelar
          </Button>
        </div>
      )}
    </div>
  );
}
