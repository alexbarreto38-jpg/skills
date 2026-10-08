"use client";

import { clsx } from "clsx";
import { Loader2 } from "lucide-react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

export const cx = clsx;

type Variant = "primary" | "secondary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg";

const VARIANT: Record<Variant, string> = {
  primary:
    "bg-accent text-white hover:bg-accent-strong shadow-[0_8px_24px_-10px_#8b6cff] disabled:bg-panel-3 disabled:text-faint disabled:shadow-none",
  secondary: "bg-panel-3 text-fg hover:bg-line-strong disabled:text-faint",
  ghost: "text-muted hover:text-fg hover:bg-panel-3",
  danger: "bg-bad/15 text-bad hover:bg-bad/25",
  outline: "border border-line-strong text-fg hover:border-accent hover:text-white",
};
const SIZE: Record<Size, string> = {
  sm: "h-8 px-3 text-xs gap-1.5",
  md: "h-9 px-4 text-sm gap-2",
  lg: "h-11 px-5 text-sm gap-2",
};

export function Button({
  variant = "secondary",
  size = "md",
  loading,
  icon,
  className,
  children,
  disabled,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: ReactNode;
}) {
  return (
    <button
      className={cx(
        "inline-flex items-center justify-center rounded-lg font-medium transition-colors disabled:cursor-not-allowed",
        VARIANT[variant],
        SIZE[size],
        className,
      )}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : icon}
      {children}
    </button>
  );
}

export function IconButton({
  label,
  className,
  children,
  active,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { label: string; active?: boolean }) {
  return (
    <button
      aria-label={label}
      title={label}
      className={cx(
        "inline-flex size-8 items-center justify-center rounded-lg text-muted transition-colors hover:bg-panel-3 hover:text-fg disabled:opacity-40 disabled:hover:bg-transparent",
        active && "bg-accent-soft text-white",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

type Tone = "neutral" | "accent" | "ok" | "warn" | "bad" | "info" | "cyan";
const TONE: Record<Tone, string> = {
  neutral: "bg-panel-3 text-muted",
  accent: "bg-accent-soft text-[#c9bcff]",
  ok: "bg-ok/15 text-ok",
  warn: "bg-warn/15 text-warn",
  bad: "bg-bad/15 text-bad",
  info: "bg-info/15 text-info",
  cyan: "bg-cyan/15 text-cyan",
};

export function Badge({ tone = "neutral", className, children }: { tone?: Tone; className?: string; children: ReactNode }) {
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-md px-1.5 py-0.5 text-[11px] font-medium leading-4",
        TONE[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function impactTone(level: string | undefined): Tone {
  return level === "HIGH" ? "bad" : level === "MEDIUM" ? "warn" : level === "LOW" ? "ok" : "neutral";
}

export function importanceTone(importance: string | undefined): Tone {
  return importance === "ESSENTIAL" ? "accent" : importance === "IMPORTANT" ? "cyan" : "neutral";
}

export function statusTone(status: string | undefined): Tone {
  if (!status) return "neutral";
  if (["COMPLETED", "READY"].includes(status)) return "ok";
  if (["FAILED", "REJECTED"].includes(status)) return "bad";
  if (["CANCELLED", "DRAFT"].includes(status)) return "neutral";
  return "info";
}

export function Progress({ value, className, tone = "accent" }: { value: number; className?: string; tone?: "accent" | "ok" | "bad" }) {
  const color = tone === "ok" ? "bg-ok" : tone === "bad" ? "bg-bad" : "bg-gradient-to-r from-accent to-cyan";
  return (
    <div className={cx("h-1.5 w-full overflow-hidden rounded-full bg-panel-3", className)}>
      <div className={cx("h-full rounded-full transition-[width] duration-500", color)} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cx("size-4 animate-spin text-muted", className)} />;
}

export function Switch({
  checked,
  onChange,
  label,
  description,
  disabled,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  description?: string;
  disabled?: boolean;
}) {
  return (
    <label className={cx("flex cursor-pointer items-start justify-between gap-3", disabled && "opacity-50")}>
      <span className="min-w-0">
        <span className="block text-sm text-fg">{label}</span>
        {description && <span className="block text-xs text-muted">{description}</span>}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cx(
          "relative mt-0.5 inline-flex h-5 w-9 shrink-0 rounded-full transition-colors",
          checked ? "bg-accent" : "bg-line-strong",
        )}
      >
        <span
          className={cx(
            "absolute top-0.5 size-4 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-4.5" : "translate-x-0.5",
          )}
        />
      </button>
    </label>
  );
}

export function Segmented<T extends string>({
  value,
  onChange,
  options,
  size = "md",
}: {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: ReactNode; hint?: string }[];
  size?: "sm" | "md";
}) {
  return (
    <div className="inline-flex rounded-lg bg-panel-2 p-0.5 ring-1 ring-line">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          title={o.hint}
          onClick={() => onChange(o.value)}
          className={cx(
            "rounded-md font-medium transition-colors",
            size === "sm" ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm",
            value === o.value ? "bg-panel-3 text-white shadow" : "text-muted hover:text-fg",
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function EmptyState({ icon, title, children }: { icon?: ReactNode; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
      {icon && <div className="mb-1 text-faint">{icon}</div>}
      <p className="text-sm font-medium text-fg">{title}</p>
      {children && <div className="max-w-sm text-xs text-muted">{children}</div>}
    </div>
  );
}

export function Input({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cx(
        "h-10 w-full rounded-lg border border-line bg-panel-2 px-3 text-sm text-fg placeholder:text-faint focus:border-accent focus:outline-none",
        className,
      )}
      {...rest}
    />
  );
}

export function Textarea({ className, ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cx(
        "w-full resize-none rounded-lg border border-line bg-panel-2 px-3 py-2 text-sm text-fg placeholder:text-faint focus:border-accent focus:outline-none",
        className,
      )}
      {...rest}
    />
  );
}

export function SectionTitle({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-2 px-1 pb-2">
      <h3 className="text-[11px] font-semibold uppercase tracking-[0.08em] text-faint">{children}</h3>
      {action}
    </div>
  );
}

export function ConfidenceBar({ value, threshold = 0.6 }: { value: number; threshold?: number }) {
  const tone = value < threshold ? "bg-bad" : value < 0.85 ? "bg-warn" : "bg-ok";
  return (
    <div className="flex items-center gap-2" title={`Confiança da análise: ${(value * 100).toFixed(0)}%`}>
      <div className="h-1 w-16 overflow-hidden rounded-full bg-panel-3">
        <div className={cx("h-full", tone)} style={{ width: `${value * 100}%` }} />
      </div>
      <span className="font-mono text-[11px] text-muted">{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="rounded border border-line-strong bg-panel-2 px-1 font-mono text-[10px] text-muted">
      {children}
    </kbd>
  );
}
