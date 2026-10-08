"use client";

import { PlugZap, RotateCw } from "lucide-react";

import { Button, EmptyState } from "@/components/ui/primitives";
import { errorMessage, isOffline } from "@/lib/api";

/** Error state for a page that could not load: says what to do and offers a retry. */
export function LoadError({ error, onRetry, title }: { error: unknown; onRetry: () => void; title?: string }) {
  const offline = isOffline(error);
  return (
    <EmptyState
      icon={<PlugZap className="size-10" />}
      title={offline ? "Não consegui me conectar ao VideoDNA" : (title ?? "Não foi possível carregar")}
    >
      <p className="mb-4 max-w-md">
        {offline
          ? "O servidor pode estar desligado ou ainda iniciando. Espere alguns segundos e clique em “Tentar de novo”. Se continuar, rode o iniciar.ps1 de novo (ou abra o Docker Desktop)."
          : errorMessage(error)}
      </p>
      <Button variant="primary" icon={<RotateCw className="size-4" />} onClick={onRetry}>
        Tentar de novo
      </Button>
    </EmptyState>
  );
}
