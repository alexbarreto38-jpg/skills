"use client";

import { Lightbulb } from "lucide-react";
import type { ReactNode } from "react";

import { cx } from "@/components/ui/primitives";
import { useHint } from "@/lib/hints";

/** A short "what to do here" note that the user can close with "Entendi". */
export function Hint({
  id,
  active = true,
  className,
  children,
}: {
  id: string;
  active?: boolean;
  className?: string;
  children: ReactNode;
}) {
  const { visible, dismiss } = useHint(id, active);
  if (!visible) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className={cx(
        "flex gap-2 rounded-xl border border-accent/40 bg-accent/10 p-3 text-xs leading-relaxed text-fg",
        className,
      )}
    >
      <Lightbulb className="mt-0.5 size-3.5 shrink-0 text-accent" />
      <div className="flex-1">{children}</div>
      <button type="button" onClick={dismiss} className="self-start text-muted underline-offset-2 hover:text-fg hover:underline">
        Entendi
      </button>
    </div>
  );
}
