export function formatMoney(value: number | null | undefined, currency = "BRL"): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(value ?? 0);
}

/** 7.4 -> "00:07.4" (timeline precision). */
export function formatTime(seconds: number | null | undefined): string {
  const s = Math.max(0, seconds ?? 0);
  const minutes = Math.floor(s / 60);
  const rest = s - minutes * 60;
  return `${String(minutes).padStart(2, "0")}:${rest.toFixed(1).padStart(4, "0")}`;
}

export function formatDuration(seconds: number | null | undefined): string {
  const s = Math.round(seconds ?? 0);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}min ${String(s % 60).padStart(2, "0")}s`;
}

export function formatBytes(bytes: number | null | undefined): string {
  const b = bytes ?? 0;
  if (b < 1024) return `${b} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = b / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${units[unit]}`;
}

export function formatPercent(value: number | null | undefined, digits = 0): string {
  return `${((value ?? 0) * 100).toFixed(digits)}%`;
}

export function formatRelative(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return "";
  const diff = Math.round((now - new Date(iso).getTime()) / 1000);
  if (diff < 60) return "agora";
  if (diff < 3600) return `há ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `há ${Math.floor(diff / 3600)} h`;
  return new Date(iso).toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
}
