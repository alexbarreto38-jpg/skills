"use client";

import { formatMoney } from "@/lib/format";
import { useAppConfig } from "@/lib/queries";

export const SIMULATED_TITLE = "Valor de exemplo — no modo demonstração nada é cobrado.";

/** True while the app runs in demo mode (no paid AI; all prices are fictitious). */
export function useDemoMode(): boolean {
  return !!useAppConfig().data?.mockMode;
}

/** A price, marked "(simulado)" in demo mode so it never reads as a real charge. */
export function Money({
  value,
  currency = "BRL",
  className,
}: {
  value: number | null | undefined;
  currency?: string;
  className?: string;
}) {
  const demo = useDemoMode();
  return (
    <span className={className} title={demo ? SIMULATED_TITLE : undefined}>
      {formatMoney(value, currency)}
      {demo && <span className="ml-1 text-[0.85em] font-normal text-faint">(simulado)</span>}
    </span>
  );
}
