"use client";

import { Activity, Dna, LogIn } from "lucide-react";
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

export function MockBadge() {
  const { data } = useAppConfig();
  if (!data?.mockMode) return null;
  return (
    <Badge tone="warn" className="uppercase tracking-wide">
      Mock mode
    </Badge>
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
