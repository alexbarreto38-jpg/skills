"use client";

import { ArrowLeft, ArrowRight, Ban, Info, Pencil, Wand2 } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { Button, EmptyState, cx } from "@/components/ui/primitives";
import { QUICK_ACTION, label } from "@/lib/labels";

import { type Change, type Notice, scenesLabel } from "./plan-text";

/** "O que vai mudar": each change once, as before → after, plus what stays as in the original. */
export function ChangeSummary({
  changes,
  totalScenes,
  kept,
  continuity,
}: {
  changes: Change[];
  totalScenes: number;
  kept: string | null;
  continuity: string | null;
}) {
  return (
    <section className="panel p-4 sm:p-5">
      <h2 className="text-base font-semibold tracking-tight">O que vai mudar</h2>
      <ul className="mt-3 space-y-1.5">
        {changes.map((c) => (
          <li key={c.key} className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 rounded-lg bg-panel-2 px-3 py-2 text-sm">
            <span className="min-w-0 flex-1">
              {c.before && (
                <>
                  <span className="text-muted">{c.before}</span>
                  <ArrowRight aria-hidden className="mx-1.5 inline size-3.5 align-[-2px] text-faint" />
                  <span className="sr-only"> vira </span>
                </>
              )}
              <span className="font-medium text-fg">{c.after}</span>
              {c.note && <span className="mt-0.5 block text-xs text-muted">Seu pedido: “{c.note}”</span>}
            </span>
            <span className="text-xs text-faint">{scenesLabel(c.scenes.length, totalScenes)}</span>
          </li>
        ))}
      </ul>
      {(kept || continuity) && (
        <div className="mt-3 space-y-1 border-t border-line pt-3 text-xs leading-relaxed text-muted">
          {kept && <p>{kept}</p>}
          {continuity && <p>{continuity}</p>}
        </div>
      )}
    </section>
  );
}

export function Stat({ icon, label: text, value, hint }: { icon: ReactNode; label: string; value: ReactNode; hint?: ReactNode }) {
  return (
    <div className="panel p-4">
      <p className="flex items-center gap-1.5 text-xs text-muted">
        {icon} {text}
      </p>
      <p className="mt-1 text-xl font-semibold tracking-tight">{value}</p>
      {hint && <p className="mt-0.5 text-xs leading-relaxed text-faint">{hint}</p>}
    </div>
  );
}

/** What stops generation, each with what to do about it. */
export function BlockingNotices({ notices, onFix }: { notices: Notice[]; onFix: (entityKey: string | null) => void }) {
  return (
    <section className="rounded-xl border border-bad/40 bg-bad/10 p-4">
      <h2 className="flex items-center gap-2 text-sm font-semibold text-bad">
        <Ban className="size-4 shrink-0" /> Antes de gerar, resolva {notices.length === 1 ? "isto" : "estes pontos"}
      </h2>
      <ul className="mt-3 space-y-2">
        {notices.map((n) => (
          <li key={n.id} className="rounded-lg bg-panel/70 p-3">
            {n.title && <p className="text-sm font-medium text-fg">{n.title}</p>}
            <p className="mt-0.5 text-sm text-fg/90">{n.text}</p>
            {n.fix && <p className="mt-1 text-xs leading-relaxed text-muted">{n.fix}</p>}
            {n.action === "editor" && (
              <Button size="sm" variant="outline" className="mt-2.5" icon={<Pencil className="size-3.5" />} onClick={() => onFix(n.entityKey)}>
                {n.actionLabel ?? "Corrigir no editor"}
              </Button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Things worth knowing that do not stop generation. */
export function Notes({ notices, onFix }: { notices: Notice[]; onFix: (entityKey: string | null) => void }) {
  return (
    <section className="panel p-4">
      <h2 className="flex items-center gap-1.5 text-sm font-medium">
        <Info className="size-4 text-warn" /> Bom saber
      </h2>
      <ul className="mt-2 space-y-2">
        {notices.map((n) => (
          <li key={n.id} className="text-xs leading-relaxed text-muted">
            {n.text}
            {n.fix && ` ${n.fix}`}
            {n.action === "editor" && (
              <button
                type="button"
                onClick={() => onFix(n.entityKey)}
                className="ml-1.5 font-medium text-accent underline-offset-2 hover:underline"
              >
                {n.actionLabel ?? "Abrir no editor"}
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

/** A labelled choice (native radios, so it works with the keyboard) with one help line under it. */
export function ChoiceGroup<T extends string>({
  name,
  legend,
  value,
  onChange,
  options,
  help,
}: {
  name: string;
  legend: string;
  value: T;
  onChange: (value: T) => void;
  options: readonly { value: T; label: string; hint?: string }[];
  help: ReactNode;
}) {
  return (
    <fieldset>
      <legend className="mb-1.5 text-sm font-medium text-fg">{legend}</legend>
      <div
        className="grid gap-1 rounded-lg bg-panel-2 p-1 ring-1 ring-line"
        style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
      >
        {options.map((o) => (
          <label key={o.value} title={o.hint} className="flex">
            <input
              type="radio"
              name={name}
              value={o.value}
              checked={value === o.value}
              onChange={() => onChange(o.value)}
              className="peer sr-only"
            />
            <span
              className={cx(
                "flex w-full cursor-pointer items-center justify-center rounded-md px-2 py-1.5 text-center text-sm font-medium leading-tight transition-colors",
                "text-muted hover:text-fg peer-checked:bg-panel-3 peer-checked:text-white peer-checked:shadow",
                "peer-focus-visible:ring-2 peer-focus-visible:ring-accent",
              )}
            >
              {o.label}
            </span>
          </label>
        ))}
      </div>
      <p className="mt-1.5 text-xs leading-relaxed text-muted">{help}</p>
    </fieldset>
  );
}

const NOTHING = {
  "no-edits": {
    title: "Você ainda não escolheu nenhuma mudança",
    text: "No editor, clique em uma pessoa, roupa, objeto ou no cenário e escolha como ele deve mudar. Depois volte aqui para gerar.",
  },
  "no-visual": {
    title: "Ainda não há nada para gerar",
    text: `Confirmar o que é um item e marcar “${label(QUICK_ACTION, "KEEP")}” ajudam a IA, mas não mudam o vídeo. Volte ao editor e escolha pelo menos uma mudança.`,
  },
  "no-scenes": {
    title: "Ainda não há nada para gerar",
    text: "As mudanças que você escolheu não aparecem em nenhuma cena do vídeo. Volte ao editor e escolha outro elemento.",
  },
} as const;

/** The dead end turned into a way back: there is nothing to generate yet. */
export function NothingToGenerate({ reason, editorHref }: { reason: keyof typeof NOTHING; editorHref: string }) {
  return (
    <div className="panel">
      <EmptyState icon={<Wand2 className="size-10" />} title={NOTHING[reason].title}>
        <p className="mb-4 max-w-md">{NOTHING[reason].text}</p>
        <BackToEditor href={editorHref} primary />
      </EmptyState>
    </div>
  );
}

export function BackToEditor({ href, primary = false }: { href: string; primary?: boolean }) {
  return (
    <Link
      href={href}
      className={cx(
        "inline-flex h-9 items-center justify-center gap-2 rounded-lg px-4 text-sm font-medium transition-colors",
        primary ? "bg-accent text-white hover:bg-accent-strong" : "border border-line-strong text-fg hover:border-accent",
      )}
    >
      <ArrowLeft className="size-4" /> Voltar ao editor
    </Link>
  );
}
