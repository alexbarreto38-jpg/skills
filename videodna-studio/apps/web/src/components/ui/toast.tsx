"use client";

import { CheckCircle2, CircleAlert, Info, X } from "lucide-react";
import { create } from "zustand";

import { cx } from "./primitives";

type ToastTone = "ok" | "bad" | "info";
interface Toast {
  id: number;
  tone: ToastTone;
  title: string;
  body?: string;
}

const useToasts = create<{ toasts: Toast[]; push: (t: Omit<Toast, "id">) => void; dismiss: (id: number) => void }>(
  (set) => ({
    toasts: [],
    push: (t) => {
      const id = Date.now() + Math.random();
      set((s) => ({ toasts: [...s.toasts.slice(-3), { ...t, id }] }));
      // An error is often the only explanation of what happened: it stays until closed.
      if (t.tone !== "bad") {
        setTimeout(() => set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) })), 8000);
      }
    },
    dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) })),
  }),
);

export const toast = {
  ok: (title: string, body?: string) => useToasts.getState().push({ tone: "ok", title, body }),
  error: (title: string, body?: string) => useToasts.getState().push({ tone: "bad", title, body }),
  info: (title: string, body?: string) => useToasts.getState().push({ tone: "info", title, body }),
};

export function ToastViewport() {
  const { toasts, dismiss } = useToasts();
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2" aria-live="polite">
      {toasts.map((t) => {
        const Icon = t.tone === "ok" ? CheckCircle2 : t.tone === "bad" ? CircleAlert : Info;
        return (
          <div
            key={t.id}
            role={t.tone === "bad" ? "alert" : "status"}
            className="pointer-events-auto flex gap-3 rounded-xl border border-line bg-panel-2 p-3 shadow-[var(--shadow-panel)]"
          >
            <Icon className={cx("mt-0.5 size-4 shrink-0", t.tone === "ok" ? "text-ok" : t.tone === "bad" ? "text-bad" : "text-info")} />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">{t.title}</p>
              {t.body && <p className="mt-0.5 text-xs text-muted">{t.body}</p>}
            </div>
            <button aria-label="Fechar" onClick={() => dismiss(t.id)} className="text-faint hover:text-fg">
              <X className="size-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
