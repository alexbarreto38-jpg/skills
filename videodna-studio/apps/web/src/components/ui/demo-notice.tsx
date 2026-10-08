"use client";

import { FlaskConical } from "lucide-react";

import { cx } from "@/components/ui/primitives";
import { useDemoMode } from "@/components/ui/money";

const TEXT = {
  upload:
    "Modo demonstração: envie qualquer vídeo para testar o caminho completo. Os cortes, quadros e cores são medidos de verdade, mas os personagens e objetos que vão aparecer são de exemplo (um menino, um copo e a mãe), não do seu vídeo.",
  editor:
    "Modo demonstração: esta história é um exemplo fixo (menino, copo e mãe) aplicado às cenas do seu vídeo. Com a IA real, ela descreve o seu vídeo.",
  result:
    "Este resultado é uma simulação: as marcações coloridas mostram onde a IA faria cada mudança. Com a IA real, o vídeo muda de verdade.",
} as const;

/** Says plainly what is simulated, where it matters. Renders nothing outside demo mode. */
export function DemoNotice({ variant, className }: { variant: keyof typeof TEXT; className?: string }) {
  const demo = useDemoMode();
  if (!demo) return null;
  return (
    <p
      className={cx(
        "flex gap-2 rounded-xl border border-warn/30 bg-warn/10 p-3 text-xs leading-relaxed text-muted",
        className,
      )}
    >
      <FlaskConical className="mt-0.5 size-3.5 shrink-0 text-warn" />
      <span>{TEXT[variant]}</span>
    </p>
  );
}
