"use client";

import type { Output } from "@videodna/api-client";
import { ArrowLeft, Columns2, Download, GitCompareArrows, History, Pause, Play, RotateCcw, SplitSquareHorizontal } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { Badge, Button, EmptyState, IconButton, Segmented, Spinner, cx } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { formatBytes, formatMoney, formatRelative, formatTime } from "@/lib/format";
import { STRATEGY, label } from "@/lib/labels";
import { useCosts, useOutputs, useProject, useRestoreVersion, useVersions } from "@/lib/queries";

type Mode = "side" | "slider" | "toggle";

export default function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id);
  const outputs = useOutputs(id);
  const versions = useVersions(id);
  const costs = useCosts(id);
  const restore = useRestoreVersion(id);
  const [mode, setMode] = useState<Mode>("slider");
  const [split, setSplit] = useState(50);
  const [showModified, setShowModified] = useState(true);
  const [outputId, setOutputId] = useState<string | null>(null);
  // Two videos driven by one clock: the modified video is the master.
  const original = useRef<HTMLVideoElement>(null);
  const modified = useRef<HTMLVideoElement>(null);
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const m = modified.current;
      const f = original.current;
      if (m) {
        setTime(m.currentTime);
        if (f && Math.abs(f.currentTime - m.currentTime) > 0.08) f.currentTime = m.currentTime;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);
  const play = () => {
    modified.current?.play();
    original.current?.play();
    setPlaying(true);
  };
  const pause = () => {
    modified.current?.pause();
    original.current?.pause();
    setPlaying(false);
  };
  const seek = (t: number) => {
    if (modified.current) modified.current.currentTime = t;
    if (original.current) original.current.currentTime = t;
    setTime(t);
  };

  const renders = useMemo(
    () => (outputs.data ?? []).filter((o) => o.kind === "FINAL" || o.kind === "PREVIEW"),
    [outputs.data],
  );
  const current: Output | undefined = renders.find((o) => o.id === outputId) ?? renders[0];
  const provenance = (current?.provenance ?? {}) as {
    shots?: { shotKey: string; strategy: string; providers: string[]; repairAttempts: number; unresolved: boolean }[];
    qualityMode?: string;
    generatedAt?: string;
    transformations?: unknown[];
    mock?: boolean;
  };
  const duration = current?.durationSec ?? project?.sourceVideo?.durationSec ?? 0;

  if (outputs.isLoading || !project) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner className="size-6" />
      </div>
    );
  }

  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <Link href={`/projects/${id}`} className="mb-4 inline-flex items-center gap-1.5 text-xs text-muted hover:text-fg">
          <ArrowLeft className="size-3.5" /> Voltar ao editor
        </Link>
        <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Original × Modificado</h1>
            <p className="mt-1 text-sm text-muted">{project.name}</p>
          </div>
          <div className="flex items-center gap-2">
            <Segmented
              value={mode}
              onChange={setMode}
              options={[
                { value: "side", label: <span className="flex items-center gap-1.5"><Columns2 className="size-3.5" /> Lado a lado</span> },
                { value: "slider", label: <span className="flex items-center gap-1.5"><SplitSquareHorizontal className="size-3.5" /> Slider</span> },
                { value: "toggle", label: <span className="flex items-center gap-1.5"><GitCompareArrows className="size-3.5" /> Alternar</span> },
              ]}
            />
            {current?.downloadUrl && (
              <a href={current.downloadUrl}>
                <Button variant="primary" icon={<Download className="size-4" />}>
                  Exportar MP4
                </Button>
              </a>
            )}
          </div>
        </div>

        {!current ? (
          <div className="panel">
            <EmptyState title="Nenhum resultado ainda">Revise as alterações e gere o vídeo para comparar.</EmptyState>
          </div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
            <section className="space-y-3">
              <div className={cx("gap-3", mode === "side" ? "grid grid-cols-2" : "block")}>
                {mode === "side" ? (
                  <>
                    <figure className="space-y-1.5">
                      <figcaption className="text-xs font-medium text-muted">ORIGINAL</figcaption>
                      <video ref={original} src={project.sourceVideo?.proxyUrl ?? undefined} poster={project.sourceVideo?.posterUrl ?? undefined} className="aspect-video w-full rounded-xl bg-black" muted playsInline />
                    </figure>
                    <figure className="space-y-1.5">
                      <figcaption className="text-xs font-medium text-[#c9bcff]">MODIFICADO</figcaption>
                      <video ref={modified} src={current.url} className="aspect-video w-full rounded-xl bg-black" playsInline />
                    </figure>
                  </>
                ) : (
                  <div className="relative aspect-video overflow-hidden rounded-xl bg-black">
                    <video ref={original} src={project.sourceVideo?.proxyUrl ?? undefined} poster={project.sourceVideo?.posterUrl ?? undefined} className="absolute inset-0 size-full" muted playsInline />
                    <video
                      ref={modified}
                      src={current.url}
                      className="absolute inset-0 size-full"
                      playsInline
                      style={
                        mode === "slider"
                          ? { clipPath: `inset(0 0 0 ${split}%)` }
                          : { opacity: showModified ? 1 : 0 }
                      }
                    />
                    {mode === "slider" && (
                      <>
                        <div className="pointer-events-none absolute inset-y-0 w-0.5 bg-white shadow" style={{ left: `${split}%` }} />
                        <input
                          aria-label="Posição da comparação"
                          type="range"
                          min={0}
                          max={100}
                          value={split}
                          onChange={(e) => setSplit(Number(e.target.value))}
                          className="absolute inset-0 size-full cursor-ew-resize opacity-0"
                        />
                        <span className="absolute left-3 top-3 rounded bg-black/70 px-2 py-0.5 text-[11px]">ORIGINAL</span>
                        <span className="absolute right-3 top-3 rounded bg-accent/80 px-2 py-0.5 text-[11px]">MODIFICADO</span>
                      </>
                    )}
                    {mode === "toggle" && (
                      <span className={cx("absolute left-3 top-3 rounded px-2 py-0.5 text-[11px]", showModified ? "bg-accent/80" : "bg-black/70")}>
                        {showModified ? "MODIFICADO" : "ORIGINAL"}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div className="panel flex items-center gap-3 px-3 py-2">
                <IconButton label={playing ? "Pausar" : "Reproduzir"} onClick={playing ? pause : play} className="bg-panel-3 text-fg">
                  {playing ? <Pause className="size-4" /> : <Play className="size-4" />}
                </IconButton>
                <input
                  aria-label="Tempo"
                  type="range"
                  min={0}
                  max={duration || 1}
                  step={0.04}
                  value={time}
                  onChange={(e) => seek(Number(e.target.value))}
                  className="flex-1 accent-[#8b6cff]"
                />
                <span className="font-mono text-xs text-muted">
                  {formatTime(time)} / {formatTime(duration)}
                </span>
                {mode === "toggle" && (
                  <div className="flex gap-1">
                    <Button size="sm" variant={!showModified ? "primary" : "secondary"} onClick={() => setShowModified(false)}>
                      ORIGINAL
                    </Button>
                    <Button size="sm" variant={showModified ? "primary" : "secondary"} onClick={() => setShowModified(true)}>
                      MODIFICADO
                    </Button>
                  </div>
                )}
              </div>
              {provenance.shots && (
                <div className="panel overflow-hidden">
                  <div className="border-b border-line px-4 py-2.5 text-sm font-medium">Shots reconstruídos</div>
                  <ul className="divide-y divide-line text-xs">
                    {provenance.shots.map((s) => (
                      <li key={s.shotKey} className="flex items-center gap-3 px-4 py-2">
                        <span className="w-16 font-mono text-faint">{s.shotKey}</span>
                        <Badge tone={s.strategy === "PASSTHROUGH" ? "neutral" : "accent"}>{label(STRATEGY, s.strategy)}</Badge>
                        <span className="min-w-0 flex-1 truncate text-muted">{s.providers.join(" → ") || "cópia do original"}</span>
                        {s.repairAttempts > 0 && <Badge tone={s.unresolved ? "bad" : "ok"}>{s.repairAttempts} reparo(s)</Badge>}
                        {s.unresolved && <span className="text-warn">Esta parte ainda apresenta inconsistência.</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            <aside className="space-y-4">
              <section className="panel space-y-2 p-4 text-sm">
                <h3 className="font-medium">Arquivo</h3>
                <p className="text-xs text-muted">
                  {current.kind === "FINAL" ? "Final" : "Preview"} · {current.width}×{current.height} · {formatBytes(current.sizeBytes)}
                </p>
                <p className="text-xs text-muted">
                  Gerado {formatRelative(current.createdAt)} · modo {provenance.qualityMode?.toLowerCase()}
                  {provenance.mock ? " · mock" : ""}
                </p>
                <p className="text-[11px] leading-relaxed text-faint">
                  Metadados privados do original (GPS, dispositivo) foram removidos. A proveniência
                  (origem, providers, transformações) fica registrada internamente.
                </p>
              </section>
              {costs.data && (
                <section className="panel space-y-1.5 p-4 text-sm">
                  <h3 className="font-medium">Custo do projeto</h3>
                  <p className="flex justify-between text-xs">
                    <span className="text-muted">Real</span>
                    <span>{formatMoney(costs.data.actualTotal, costs.data.currency)}</span>
                  </p>
                  <p className="flex justify-between text-xs">
                    <span className="text-muted">Estimado (planos executados)</span>
                    <span>{formatMoney(costs.data.estimatedTotal, costs.data.currency)}</span>
                  </p>
                  <p className="flex justify-between text-xs">
                    <span className="text-muted">Segundos gerados</span>
                    <span>{costs.data.secondsGenerated.toFixed(1)}s</span>
                  </p>
                </section>
              )}
              <section className="panel p-4">
                <h3 className="mb-2 flex items-center gap-1.5 text-sm font-medium">
                  <History className="size-4" /> Versões
                </h3>
                <ul className="space-y-1.5">
                  {(versions.data ?? []).map((v) => (
                    <li key={v.id} className={cx("rounded-lg border px-2.5 py-2 text-xs", v.outputId === current.id ? "border-accent/60 bg-accent-soft/40" : "border-line")}>
                      <div className="flex items-center justify-between gap-2">
                        <button type="button" className="min-w-0 truncate text-left hover:text-white" onClick={() => v.outputId && setOutputId(v.outputId)} disabled={!v.outputId}>
                          v{v.number} · {v.name}
                        </button>
                        <IconButton
                          label="Restaurar estas alterações no editor"
                          onClick={() => restore.mutate(v.id, { onSuccess: () => toast.ok(`Versão ${v.number} restaurada no editor`) })}
                        >
                          <RotateCcw className="size-3.5" />
                        </IconButton>
                      </div>
                      <p className="text-faint">
                        {v.operationCount} alteração(ões) · {formatRelative(v.createdAt)}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
