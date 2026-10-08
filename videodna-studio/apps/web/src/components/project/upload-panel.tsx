"use client";

import { useQueryClient } from "@tanstack/react-query";
import { FileVideo, ShieldCheck, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

import { DemoNotice } from "@/components/ui/demo-notice";
import { Button, Progress, cx } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { formatBytes } from "@/lib/format";
import { keys, useAppConfig } from "@/lib/queries";
import { type UploadProgress, uploadVideo } from "@/lib/upload";

/** Tela 1: envio do vídeo com confirmação de direitos de uso (spec §54). */
export function UploadPanel({ projectId, onDone }: { projectId: string; onDone?: (jobId: string | null) => void }) {
  const { data: config } = useAppConfig();
  const qc = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [rights, setRights] = useState(false);
  const [drag, setDrag] = useState(false);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [busy, setBusy] = useState(false);

  const accept = config?.uploadAllowedContentTypes.join(",") ?? "video/*";
  const tooBig = !!file && !!config && file.size > config.uploadMaxBytes;

  async function start() {
    if (!file) return;
    setBusy(true);
    try {
      const done = await uploadVideo(projectId, file, { onProgress: setProgress });
      await qc.invalidateQueries({ queryKey: keys.project(projectId) });
      toast.ok("Vídeo enviado", "A análise começou.");
      onDone?.(done.job?.id ?? null);
    } catch (e) {
      toast.error("Falha no upload", `${errorMessage(e)} Tente novamente — as partes já enviadas não serão reenviadas.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={() => input.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const dropped = e.dataTransfer.files?.[0];
          if (dropped) setFile(dropped);
        }}
        className={cx(
          "flex w-full flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed px-6 py-12 text-center transition-colors",
          drag ? "border-accent bg-accent-soft" : "border-line-strong hover:border-accent/70 hover:bg-panel-2",
        )}
      >
        {file ? (
          <>
            <FileVideo className="size-10 text-accent" />
            <div>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted">
                {formatBytes(file.size)} · {file.type || "tipo desconhecido"}
              </p>
            </div>
          </>
        ) : (
          <>
            <UploadCloud className="size-10 text-faint" />
            <div>
              <p className="text-sm font-medium">Arraste o vídeo aqui ou clique para escolher</p>
              <p className="text-xs text-muted">
                MP4, MOV, WebM ou MKV · até {formatBytes(config?.uploadMaxBytes)} ·{" "}
                {Math.round((config?.videoMaxDurationSec ?? 600) / 60)} min
              </p>
            </div>
          </>
        )}
      </button>
      <input
        ref={input}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
      />
      {tooBig && <p className="text-xs text-bad">O arquivo excede o tamanho máximo permitido.</p>}

      <DemoNotice variant="upload" />

      <label className="flex cursor-pointer gap-3 rounded-xl border border-line bg-panel-2 p-3 text-xs leading-relaxed text-muted">
        <input
          type="checkbox"
          checked={rights}
          onChange={(e) => setRights(e.target.checked)}
          className="mt-0.5 size-4 shrink-0 accent-[#8b6cff]"
        />
        <span>
          <span className="mb-1 flex items-center gap-1.5 font-medium text-fg">
            <ShieldCheck className="size-3.5 text-ok" /> Direitos de uso
          </span>
          {config?.rightsStatement ??
            "Declaro que possuo os direitos ou autorização para transformar este vídeo."}
        </span>
      </label>

      {progress && (
        <div className="space-y-1.5">
          <Progress value={(progress.loaded / Math.max(1, progress.total)) * 100} />
          <p className="flex justify-between text-xs text-muted">
            <span>
              Parte {progress.part}/{progress.parts}
            </span>
            <span>
              {formatBytes(progress.loaded)} de {formatBytes(progress.total)}
            </span>
          </p>
        </div>
      )}

      <Button
        variant="primary"
        size="lg"
        className="w-full"
        disabled={!file || !rights || tooBig}
        loading={busy}
        onClick={start}
        icon={<UploadCloud className="size-4" />}
      >
        Enviar e analisar
      </Button>
    </div>
  );
}
