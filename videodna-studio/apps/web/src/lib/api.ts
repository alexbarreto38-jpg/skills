import {
  ApiError,
  type ClientOptions,
  createApiClient,
  streamJobEvents,
  unwrap,
} from "@videodna/api-client";

export { ApiError, unwrap };

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

const TOKEN_KEY = "videodna.token";

/** Token lives in localStorage as a per-browser convenience; every access is
 * guarded because storage can be unavailable (private mode, blocked cookies). */
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: session-only auth */
  }
}

const options: ClientOptions = {
  baseUrl: API_URL,
  getToken,
  onUnauthorized: () => {
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      const next = encodeURIComponent(window.location.pathname);
      // Outside React (no router here): a full navigation to the login page is intended.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign(`${window.location.origin}/login?next=${next}`);
    }
  },
};

export const api = createApiClient(options);

export function streamJob(
  jobId: string,
  onEvent: Parameters<typeof streamJobEvents>[0]["onEvent"],
  signal?: AbortSignal,
  after = -1,
) {
  return streamJobEvents({ ...options, jobId, onEvent, signal, after });
}

export const OFFLINE_MESSAGE =
  "Não consegui me conectar ao VideoDNA. O servidor pode estar desligado ou ainda iniciando — espere alguns segundos e tente de novo.";

/** True when the API could not be reached at all (server down, starting, or no network). */
export function isOffline(error: unknown): boolean {
  // A gateway error without our JSON body (no requestId) means the API itself is not answering.
  if (error instanceof ApiError) return [502, 503, 504].includes(error.status) && !error.requestId;
  // fetch() rejects with a TypeError ("Failed to fetch", "NetworkError…") when nothing answers.
  return error instanceof TypeError;
}

export function errorMessage(error: unknown): string {
  if (isOffline(error)) return OFFLINE_MESSAGE;
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Algo deu errado. Tente de novo.";
}
