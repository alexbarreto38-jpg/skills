/**
 * Typed VideoDNA API client.
 *
 * `schema.d.ts` is generated from the backend's OpenAPI document
 * (`pnpm gen:api`) — never edit it by hand. This file adds auth, normalized
 * errors and a Server-Sent Events reader on top of openapi-fetch.
 */
import createClient, { type Middleware } from "openapi-fetch";

import type { components, paths } from "./schema";

export type { components, paths };

type Schemas = components["schemas"];
export type Project = Schemas["ProjectOut"];
export type SourceVideo = Schemas["SourceVideoOut"];
export type Job = Schemas["JobOut"];
export type JobEvent = Schemas["JobEventOut"];
export type VideoDNAResponse = Schemas["VideoDNAResponse"];
export type VideoDNA = Schemas["VideoDNA"];
export type DnaEntity = Schemas["Entity"];
export type Shot = Schemas["Shot"];
export type Scene = Schemas["Scene"];
export type Action = Schemas["Action"];
export type EntityTrack = Schemas["EntityTrack"];
export type EntityOut = Schemas["EntityOut"];
export type EditCategory = Schemas["EditCategoryOut"];
export type Suggestion = Schemas["SuggestionOut"];
export type SuggestionList = Schemas["SuggestionList"];
export type EditCreate = Schemas["EditCreate"];
export type EditOut = Schemas["EditOut"];
export type EditResult = Schemas["EditResult"];
export type EditHistory = Schemas["EditHistoryOut"];
export type ImpactReport = Schemas["ImpactReport"];
export type Plan = Schemas["PlanOut"];
export type Output = Schemas["OutputOut"];
export type QAReport = Schemas["QAReportOut"];
export type Version = Schemas["VersionOut"];
export type CostSummary = Schemas["CostSummaryOut"];
export type AppConfig = Schemas["AppConfigOut"];
export type ProviderInfo = Schemas["ProviderOut"];
export type Metrics = Schemas["MetricsOut"];
export type ProjectSettings = Schemas["ProjectSettings-Output"];
export type ProjectSettingsInput = Schemas["ProjectSettings-Input"];
export type QualityMode = Schemas["QualityMode"];
export type UploadInit = Schemas["UploadInitResponse"];

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  requestId?: string | null;
}

/** Normalized error: the backend never leaks raw provider errors. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: Record<string, unknown>;
  readonly requestId?: string | null;

  constructor(status: number, body: ApiErrorBody | undefined) {
    super(body?.message ?? `Erro ${status}`);
    this.status = status;
    this.code = body?.code ?? "INTERNAL_ERROR";
    this.details = body?.details ?? {};
    this.requestId = body?.requestId;
  }
}

export interface ClientOptions {
  baseUrl: string;
  getToken?: () => string | null | undefined;
  onUnauthorized?: () => void;
}

export function createApiClient({ baseUrl, getToken, onUnauthorized }: ClientOptions) {
  const client = createClient<paths>({ baseUrl });
  const auth: Middleware = {
    onRequest({ request }) {
      const token = getToken?.();
      if (token) request.headers.set("Authorization", `Bearer ${token}`);
      return request;
    },
    onResponse({ response }) {
      if (response.status === 401) onUnauthorized?.();
      return response;
    },
  };
  client.use(auth);
  return client;
}

export type ApiClient = ReturnType<typeof createApiClient>;

/** Unwrap an openapi-fetch result, throwing a typed ApiError on failure. */
export async function unwrap<T>(
  promise: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await promise;
  if (error !== undefined || !response.ok) {
    const body = (error as { error?: ApiErrorBody } | undefined)?.error;
    throw new ApiError(response.status, body);
  }
  return data as T;
}

/**
 * Read a job's Server-Sent Events stream with fetch (EventSource cannot send
 * an Authorization header). Resolves when the server sends `event: end`.
 */
export async function streamJobEvents(
  opts: ClientOptions & {
    jobId: string;
    after?: number;
    signal?: AbortSignal;
    onEvent: (event: JobEvent) => void;
  },
): Promise<void> {
  const headers: Record<string, string> = { Accept: "text/event-stream" };
  const token = opts.getToken?.();
  if (token) headers.Authorization = `Bearer ${token}`;
  const url = `${opts.baseUrl}/jobs/${opts.jobId}/events?after=${opts.after ?? -1}`;
  const response = await fetch(url, { headers, signal: opts.signal });
  if (!response.ok || !response.body) {
    throw new ApiError(response.status, undefined);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) return;
    buffer += decoder.decode(value, { stream: true });
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const parsed = parseSseBlock(block);
      if (parsed.event === "end") return;
      if (parsed.event === "progress" && parsed.data) {
        opts.onEvent(JSON.parse(parsed.data) as JobEvent);
      }
      boundary = buffer.indexOf("\n\n");
    }
  }
}

export function parseSseBlock(block: string): { event?: string; data?: string; id?: string } {
  const out: { event?: string; data?: string; id?: string } = {};
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (!line || line.startsWith(":")) continue;
    const idx = line.indexOf(":");
    const field = idx === -1 ? line : line.slice(0, idx);
    const value = idx === -1 ? "" : line.slice(idx + 1).replace(/^ /, "");
    if (field === "event") out.event = value;
    else if (field === "data") data.push(value);
    else if (field === "id") out.id = value;
  }
  if (data.length) out.data = data.join("\n");
  return out;
}
