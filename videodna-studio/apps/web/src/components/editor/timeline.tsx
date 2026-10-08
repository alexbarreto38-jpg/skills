"use client";

import type { QAReport, VideoDNA } from "@videodna/api-client";
import { useMemo, useRef } from "react";

import { cx } from "@/components/ui/primitives";
import { modifiedShots } from "@/lib/dna";
import { useEditor } from "@/lib/editor-store";
import { formatTime } from "@/lib/format";

const AUDIO_COLOR: Record<string, string> = {
  speech: "bg-cyan/60",
  sfx: "bg-warn/70",
  music: "bg-accent/60",
  ambience: "bg-line-strong",
  silence: "bg-transparent",
};

/** Bottom panel: shots, edits, actions, audio and QA problem regions. */
export function Timeline({
  dna,
  assetUrls,
  qaReports,
}: {
  dna: VideoDNA;
  assetUrls: Record<string, string>;
  qaReports?: QAReport[];
}) {
  const { currentTime, seek, selectShot, selectedShot } = useEditor();
  const track = useRef<HTMLDivElement>(null);
  const duration = dna.technical.durationSec || 1;
  const modified = useMemo(() => modifiedShots(dna), [dna]);
  const pct = (t: number) => `${(t / duration) * 100}%`;
  const issues = (qaReports ?? []).flatMap((r) => r.issues ?? []);

  function seekFromEvent(clientX: number) {
    const rect = track.current?.getBoundingClientRect();
    if (!rect) return;
    seek(Math.max(0, Math.min(duration, ((clientX - rect.left) / rect.width) * duration)));
  }

  const ticks = Array.from({ length: Math.floor(duration) + 1 }, (_, i) => i).filter(
    (s) => s % (duration > 60 ? 10 : duration > 20 ? 5 : 1) === 0,
  );

  const row = (name: string, height: string, children: React.ReactNode) => (
    <div className="flex items-center">
      <span className="w-20 shrink-0 pr-3 text-right text-[10px] font-medium uppercase tracking-wide text-faint">{name}</span>
      <div className={cx("relative flex-1", height)}>{children}</div>
    </div>
  );

  return (
    <div className="flex h-full flex-col gap-1.5 px-4 py-2 select-none">
      <div className="relative ml-20 h-4 text-[10px] text-faint">
        {ticks.map((t) => (
          <span key={t} className="absolute -translate-x-1/2 font-mono" style={{ left: pct(t) }}>
            {formatTime(t).slice(0, 5)}
          </span>
        ))}
      </div>
      <div className="relative flex cursor-pointer flex-col gap-1.5" onMouseDown={(e) => seekFromEvent(e.clientX)}>
        {row(
          "Shots",
          "h-14",
          dna.shots.map((s) => {
            const thumb = s.thumbnailKey ? assetUrls[s.thumbnailKey] : undefined;
            return (
              <button
                key={s.id}
                type="button"
                title={`${s.id} · ${formatTime(s.startTime)}–${formatTime(s.endTime)} · ${s.camera?.shotSize ?? ""}`}
                onMouseDown={(e) => {
                  e.stopPropagation();
                  selectShot(s.id);
                  seek(s.startTime + 0.04);
                }}
                className={cx(
                  "absolute inset-y-0 overflow-hidden rounded-md border bg-panel-3 bg-cover bg-center",
                  selectedShot === s.id ? "border-white" : "border-line",
                )}
                style={{
                  left: `calc(${pct(s.startTime)} + 1px)`,
                  width: `calc(${pct(s.endTime - s.startTime)} - 2px)`,
                  backgroundImage: thumb ? `url(${thumb})` : undefined,
                }}
              >
                <span className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                {modified.has(s.id) && <span className="absolute inset-x-0 top-0 h-1 bg-accent" />}
                <span className="absolute bottom-1 left-1.5 font-mono text-[10px] text-white/90">{s.id.replace("SHOT_", "#")}</span>
              </button>
            );
          }),
        )}
        {row(
          "Ações",
          "h-3",
          dna.actions.map((a) => (
            <span
              key={a.id}
              title={a.label}
              className={cx("absolute inset-y-0 rounded-sm border-r border-bg", a.essential ? "bg-accent/70" : "bg-line-strong")}
              style={{ left: pct(a.startTime), width: `max(4px, ${pct(a.endTime - a.startTime)})` }}
            />
          )),
        )}
        {row(
          "Áudio",
          "h-2.5",
          dna.audio.segments?.map((seg) => (
            <span
              key={seg.id}
              title={seg.transcript ?? seg.label ?? seg.kind}
              className={cx("absolute inset-y-0 rounded-sm", AUDIO_COLOR[seg.kind] ?? "bg-line")}
              style={{ left: pct(seg.startTime), width: `max(3px, ${pct(seg.endTime - seg.startTime)})` }}
            />
          )),
        )}
        {row(
          "QA",
          "h-2.5",
          issues.map((i) => (
            <span
              key={i.id}
              title={`${i.description} (${i.status})`}
              className={cx(
                "absolute inset-y-0 rounded-sm",
                i.status === "REPAIRED" ? "bg-ok/60" : i.status === "UNRESOLVED" ? "bg-bad" : "bg-warn",
              )}
              style={{ left: pct(i.startTime), width: `max(4px, ${pct(i.endTime - i.startTime)})` }}
            />
          )),
        )}
        <div ref={track} className="pointer-events-none absolute inset-y-0 left-20 right-0">
          <div className="absolute inset-y-0 w-px bg-white" style={{ left: pct(currentTime) }}>
            <span className="absolute -left-1 -top-1 size-2 rounded-full bg-white" />
          </div>
        </div>
      </div>
    </div>
  );
}
