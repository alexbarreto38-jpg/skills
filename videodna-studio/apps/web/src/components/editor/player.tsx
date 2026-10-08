"use client";

import type { VideoDNA } from "@videodna/api-client";
import { Eye, EyeOff, Pause, Play, SkipBack, SkipForward } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { IconButton, cx } from "@/components/ui/primitives";
import { entityMap, isModified, visibleBoxes } from "@/lib/dna";
import { useEditor } from "@/lib/editor-store";
import { formatTime } from "@/lib/format";

/** Center panel: proxy video + clickable overlay of tracked elements. */
export function Player({
  src,
  poster,
  dna,
  showClickHint = false,
}: {
  src?: string | null;
  poster?: string | null;
  dna?: VideoDNA;
  /** First-time cue that the boxes over the video are clickable. */
  showClickHint?: boolean;
}) {
  const video = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [duration, setDuration] = useState(dna?.technical.durationSec ?? 0);
  const { currentTime, setTime, seekRequest, selectedKey, select, showBoxes, toggleBoxes } = useEditor();
  const [hovered, setHovered] = useState<string | null>(null);
  const entities = useMemo(() => entityMap(dna), [dna]);

  // Smooth overlay while playing: sample the clock every frame.
  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    const tick = () => {
      if (video.current) setTime(video.current.currentTime);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing, setTime]);

  useEffect(() => {
    if (seekRequest && video.current) video.current.currentTime = seekRequest.time;
  }, [seekRequest]);

  const boxes = useMemo(
    () => (showBoxes ? visibleBoxes(dna, currentTime, selectedKey) : []),
    [dna, currentTime, showBoxes, selectedKey],
  );
  const fps = dna?.technical.fps ?? 25;
  const ratio = dna && dna.technical.height ? dna.technical.width / dna.technical.height : 16 / 9;

  // The frame must match the video exactly: the boxes are positioned in % of the
  // frame, so any letterboxing (a vertical phone video in a wide panel) would put
  // them on the black bars. CSS alone cannot fit both width and height here.
  const stage = useRef<HTMLDivElement>(null);
  const [frame, setFrame] = useState<{ w: number; h: number } | null>(null);
  useEffect(() => {
    const el = stage.current;
    if (!el) return;
    const observer = new ResizeObserver(() => {
      const padding = 32; // p-4 on both sides
      const w = el.clientWidth - padding;
      const h = el.clientHeight - padding;
      if (w <= 0 || h <= 0) return;
      const width = Math.min(w, h * ratio);
      setFrame({ w: width, h: width / ratio });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [ratio]);

  function step(frames: number) {
    if (!video.current) return;
    video.current.pause();
    video.current.currentTime = Math.max(0, Math.min(duration, video.current.currentTime + frames / fps));
    setTime(video.current.currentTime);
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={stage} className="flex min-h-0 flex-1 items-center justify-center p-4">
        <div
          className="relative overflow-hidden rounded-xl bg-black shadow-[var(--shadow-panel)]"
          style={frame ? { width: frame.w, height: frame.h } : { aspectRatio: ratio, width: "100%" }}
        >
          {src ? (
            <video
              ref={video}
              src={src}
              poster={poster ?? undefined}
              className="absolute inset-0 size-full"
              preload="auto"
              playsInline
              onPlay={() => setPlaying(true)}
              onPause={() => setPlaying(false)}
              onTimeUpdate={(e) => !playing && setTime(e.currentTarget.currentTime)}
              onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
              onClick={(e) => (e.currentTarget.paused ? e.currentTarget.play() : e.currentTarget.pause())}
            />
          ) : (
            <div className="checker absolute inset-0" />
          )}
          <div className="pointer-events-none absolute inset-0">
            {boxes.map((b) => {
              const entity = entities.get(b.entityKey);
              const selected = b.entityKey === selectedKey;
              const modified = isModified(entity);
              const review = entity?.needsReview;
              return (
                <button
                  key={`${b.entityKey}`}
                  type="button"
                  onMouseEnter={() => setHovered(b.entityKey)}
                  onMouseLeave={() => setHovered(null)}
                  onClick={(e) => {
                    e.stopPropagation();
                    select(b.entityKey);
                  }}
                  className={cx(
                    "pointer-events-auto absolute rounded-[4px] border transition-colors",
                    selected
                      ? "border-2 border-white bg-white/10"
                      : modified
                        ? "border-accent bg-accent/10"
                        : review
                          ? "border-dashed border-warn/80 hover:bg-warn/10"
                          : "border-white/25 hover:border-white/80 hover:bg-white/5",
                    b.occluded && !selected && "border-dotted",
                  )}
                  style={{ left: `${b.x * 100}%`, top: `${b.y * 100}%`, width: `${b.w * 100}%`, height: `${b.h * 100}%` }}
                  aria-label={entity?.label ?? b.entityKey}
                >
                  {(selected || hovered === b.entityKey) && (
                    <span className="absolute -top-6 left-0 whitespace-nowrap rounded bg-black/80 px-1.5 py-0.5 text-[11px] text-white">
                      {entity?.label ?? b.entityKey}
                      {review ? " · ?" : ""}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
          {showClickHint && showBoxes && (
            <span className="pointer-events-none absolute bottom-3 left-3 rounded-full bg-black/75 px-3 py-1 text-xs text-white">
              As caixas sobre o vídeo também são clicáveis
            </span>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 border-t border-line px-4 py-2">
        <IconButton label="Quadro anterior" onClick={() => step(-1)}>
          <SkipBack className="size-4" />
        </IconButton>
        <IconButton
          label={playing ? "Pausar" : "Reproduzir"}
          onClick={() => (video.current?.paused ? video.current.play() : video.current?.pause())}
          className="bg-panel-3 text-fg"
        >
          {playing ? <Pause className="size-4" /> : <Play className="size-4" />}
        </IconButton>
        <IconButton label="Próximo quadro" onClick={() => step(1)}>
          <SkipForward className="size-4" />
        </IconButton>
        <span className="ml-2 font-mono text-xs text-muted">
          {formatTime(currentTime)} <span className="text-faint">/ {formatTime(duration)}</span>
        </span>
        <div className="flex-1" />
        <IconButton label={showBoxes ? "Ocultar elementos" : "Mostrar elementos"} onClick={toggleBoxes} active={showBoxes}>
          {showBoxes ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
        </IconButton>
      </div>
    </div>
  );
}
