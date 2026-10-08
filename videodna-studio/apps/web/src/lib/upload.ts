import type { UploadInit } from "@videodna/api-client";

import { api, unwrap } from "./api";

export interface UploadProgress {
  loaded: number;
  total: number;
  part: number;
  parts: number;
}

/** PUT one part with real byte-level progress (fetch cannot report upload progress). */
function putPart(url: string, blob: Blob, onBytes: (loaded: number) => void, signal?: AbortSignal) {
  return new Promise<string>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    xhr.upload.onprogress = (e) => onBytes(e.loaded);
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const etag = xhr.getResponseHeader("ETag") ?? xhr.getResponseHeader("etag");
        if (!etag) reject(new Error("O storage não retornou ETag (verifique o CORS)."));
        else resolve(etag.replaceAll('"', ""));
      } else reject(new Error(`Falha no envio da parte (${xhr.status}).`));
    };
    xhr.onerror = () => reject(new Error("Erro de rede durante o upload."));
    signal?.addEventListener("abort", () => xhr.abort());
    xhr.send(blob);
  });
}

/**
 * Multipart upload straight to storage via signed URLs, resumable: parts that
 * already arrived (per the server) are skipped, so a retry after a network
 * failure only sends what is missing.
 */
export async function uploadVideo(
  projectId: string,
  file: File,
  {
    onProgress,
    signal,
    resume,
  }: { onProgress?: (p: UploadProgress) => void; signal?: AbortSignal; resume?: UploadInit } = {},
) {
  const init =
    resume ??
    (await unwrap(
      api.POST("/projects/{project_id}/uploads", {
        params: { path: { project_id: projectId } },
        body: {
          filename: file.name,
          contentType: file.type || "video/mp4",
          sizeBytes: file.size,
          rightsConfirmed: true,
        },
      }),
    ));
  const status = await unwrap(
    api.GET("/projects/{project_id}/uploads/{upload_id}", {
      params: { path: { project_id: projectId, upload_id: init.uploadId } },
    }),
  );
  const done = new Map(status.uploadedParts.map((p) => [p.partNumber, p.etag]));
  const urls = status.parts.length ? status.parts : init.parts;
  let loadedBefore = [...done.keys()].reduce(
    (sum, n) => sum + Math.min(init.partSize, file.size - (n - 1) * init.partSize),
    0,
  );
  for (const part of urls) {
    if (done.has(part.partNumber)) continue;
    const start = (part.partNumber - 1) * init.partSize;
    const blob = file.slice(start, Math.min(file.size, start + init.partSize));
    const etag = await putPart(
      part.url,
      blob,
      (bytes) =>
        onProgress?.({ loaded: loadedBefore + bytes, total: file.size, part: part.partNumber, parts: init.partCount }),
      signal,
    );
    done.set(part.partNumber, etag);
    loadedBefore += blob.size;
  }
  onProgress?.({ loaded: file.size, total: file.size, part: init.partCount, parts: init.partCount });
  return unwrap(
    api.POST("/projects/{project_id}/uploads/{upload_id}/complete", {
      params: { path: { project_id: projectId, upload_id: init.uploadId } },
      body: {
        parts: [...done.entries()].map(([partNumber, etag]) => ({ partNumber, etag })),
        analyze: true,
      },
    }),
  );
}
