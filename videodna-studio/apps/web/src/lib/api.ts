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

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Algo deu errado.";
}
