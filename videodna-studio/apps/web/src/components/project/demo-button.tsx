"use client";

import { PlayCircle } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { useAppConfig, useCreateDemoProject } from "@/lib/queries";

/**
 * Opens the example project (creating it the first time) and goes straight to it.
 * Demo mode only: with real AI the sample video would spend credits on coloured boxes.
 */
export function DemoButton({
  variant = "primary",
  size = "md",
  fresh = false,
  className,
  children,
}: {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "lg";
  /** Start a new copy even if an example project already exists. */
  fresh?: boolean;
  className?: string;
  children?: React.ReactNode;
}) {
  const router = useRouter();
  const { data: config } = useAppConfig();
  const demo = useCreateDemoProject();
  if (!config?.mockMode) return null;
  return (
    <Button
      variant={variant}
      size={size}
      className={className}
      icon={<PlayCircle className="size-4" />}
      loading={demo.isPending}
      onClick={() =>
        demo.mutate(fresh, {
          onSuccess: (created) => {
            if (created.reused) toast.ok("Abrimos o exemplo que você já tinha");
            else toast.ok("Vídeo de exemplo pronto", "Estamos analisando — leva menos de 1 minuto.");
            router.push(`/projects/${created.project.id}`);
          },
          onError: (e) =>
            toast.error("Não foi possível abrir o exemplo", `${errorMessage(e)} Tente de novo ou envie seu próprio vídeo.`),
        })
      }
    >
      {demo.isPending ? "Preparando o vídeo de exemplo…" : (children ?? "Experimentar com um vídeo de exemplo")}
    </Button>
  );
}
