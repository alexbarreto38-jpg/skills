"use client";

import { Activity, Dna, FlaskConical, LogIn } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/primitives";
import { useAppConfig } from "@/lib/queries";

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2">
      <span className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-cyan">
        <Dna className="size-4.5 text-white" />
      </span>
      <span className="text-sm font-semibold tracking-tight">
        VideoDNA <span className="text-gradient">Studio</span>
      </span>
    </Link>
  );
}

/** "Modo demonstração": click to see what is simulated. */
export function MockBadge() {
  const { data } = useAppConfig();
  if (!data?.mockMode) return null;
  return (
    <details className="group relative">
      <summary className="list-none cursor-pointer [&::-webkit-details-marker]:hidden">
        <Badge tone="warn" className="gap-1">
          <FlaskConical className="size-3" /> Modo demonstração
        </Badge>
      </summary>
      <div className="absolute left-0 top-8 z-40 w-80 rounded-xl border border-line-strong bg-panel-2 p-4 text-xs leading-relaxed text-muted shadow-2xl">
        <p className="mb-2 text-sm font-medium text-fg">Você está testando sem IA paga</p>
        <ul className="list-disc space-y-1.5 pl-4">
          <li>Os cortes, quadros e cores do vídeo são medidos de verdade.</li>
          <li>
            A parte de IA é simulada: a análise sempre conta a mesma história de exemplo (um menino, um copo e a
            mãe).
          </li>
          <li>Ao gerar, o sistema desenha marcações coloridas sobre o vídeo original para mostrar onde cada mudança aconteceria.</li>
          <li>Todos os valores em R$ são fictícios. Nada é cobrado.</li>
        </ul>
      </div>
    </details>
  );
}

export function AppHeader({ children }: { children?: React.ReactNode }) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-bg/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <Logo />
        <MockBadge />
        <div className="flex-1" />
        {children}
        <Link href="/admin" className="text-muted hover:text-fg" title="Painel interno">
          <Activity className="size-4" />
        </Link>
        <Link href="/login" className="text-muted hover:text-fg" title="Conta">
          <LogIn className="size-4" />
        </Link>
      </div>
    </header>
  );
}
