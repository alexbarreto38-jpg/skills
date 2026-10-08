import { useSyncExternalStore } from "react";

/**
 * First-time hints. Each hint is shown while its condition holds (derived from
 * server state, so it disappears on its own once the user acts) and until the
 * user clicks "Entendi". Dismissals are a per-browser convenience in
 * localStorage; every access is guarded so the page works without storage.
 */
const KEY = "videodna.hints.v1";
const EMPTY: ReadonlySet<string> = new Set();
const listeners = new Set<() => void>();
let cache: ReadonlySet<string> | null = null;

function read(): ReadonlySet<string> {
  if (cache) return cache;
  try {
    const raw = window.localStorage.getItem(KEY);
    cache = new Set(raw ? (JSON.parse(raw) as string[]) : []);
  } catch {
    cache = new Set();
  }
  return cache;
}

function write(next: ReadonlySet<string>): void {
  cache = next;
  try {
    window.localStorage.setItem(KEY, JSON.stringify([...next]));
  } catch {
    /* storage unavailable: dismissal lasts until reload */
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function useDismissed(): ReadonlySet<string> {
  return useSyncExternalStore(subscribe, read, () => EMPTY);
}

export function useHint(id: string, active: boolean): { visible: boolean; dismiss: () => void } {
  const dismissed = useDismissed();
  return { visible: active && !dismissed.has(id), dismiss: () => write(new Set([...read(), id])) };
}

/** True when the user closed at least one hint (so "Mostrar dicas de novo" makes sense). */
export function useAnyHintDismissed(): boolean {
  return useDismissed().size > 0;
}

export function resetHints(): void {
  write(new Set());
}
