"use client";

import type { QualityMode } from "@videodna/api-client";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppHeader } from "@/components/app-header";
import { DemoButton } from "@/components/project/demo-button";
import { UploadPanel } from "@/components/project/upload-panel";
import { Button, Input, Segmented } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { api, errorMessage, unwrap } from "@/lib/api";
import { QUALITY_MODE } from "@/lib/labels";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [mode, setMode] = useState<QualityMode>("BALANCED");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function create() {
    setCreating(true);
    try {
      const project = await unwrap(
        api.POST("/projects", {
          body: { name: name.trim() || "Projeto sem título", settings: { qualityMode: mode } },
        }),
      );
      setProjectId(project.id);
    } catch (e) {
      toast.error("Não foi possível criar o projeto", errorMessage(e));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-xl px-4 py-10">
        <Link href="/" className="mb-6 inline-flex items-center gap-1.5 text-xs text-muted hover:text-fg">
          <ArrowLeft className="size-3.5" /> Projetos
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">Novo projeto</h1>
        <p className="mt-1 text-sm text-muted">
          Dê um nome, escolha o modo de qualidade padrão e envie o vídeo de referência.
        </p>

        <div className="panel mt-6 flex flex-col gap-3 p-4 sm:flex-row sm:items-center">
          <p className="flex-1 text-xs leading-relaxed text-muted">
            <span className="block text-sm font-medium text-fg">Primeira vez aqui?</span>
            Use o vídeo de exemplo e veja o caminho inteiro sem precisar enviar nada.
          </p>
          <DemoButton variant="secondary" size="sm" />
        </div>

        <div className="panel mt-6 space-y-5 p-5">
          <div className="space-y-2">
            <label htmlFor="name" className="text-xs font-medium text-muted">
              Nome do projeto
            </label>
            <Input
              id="name"
              placeholder="Ex.: Comercial — versão praia"
              value={name}
              disabled={!!projectId}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <span className="text-xs font-medium text-muted">Modo de qualidade padrão</span>
            <div>
              <Segmented
                value={mode}
                onChange={setMode}
                options={(["ECONOMY", "BALANCED", "MAX"] as const).map((m) => ({
                  value: m,
                  label: QUALITY_MODE[m].label,
                  hint: QUALITY_MODE[m].hint,
                }))}
              />
            </div>
            <p className="text-xs text-faint">{QUALITY_MODE[mode].hint}. Você pode mudar antes de cada geração.</p>
          </div>
          {!projectId ? (
            <Button variant="primary" size="lg" className="w-full" loading={creating} onClick={create}>
              Continuar
            </Button>
          ) : (
            <UploadPanel projectId={projectId} onDone={() => router.push(`/projects/${projectId}`)} />
          )}
        </div>
      </main>
    </div>
  );
}
