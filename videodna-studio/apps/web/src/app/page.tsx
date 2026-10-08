"use client";

import type { Project } from "@videodna/api-client";
import { Clapperboard, Copy, Film, Plus, Sparkles, Trash2, Upload } from "lucide-react";
import Link from "next/link";

import { AppHeader } from "@/components/app-header";
import { DemoButton } from "@/components/project/demo-button";
import { Badge, Button, EmptyState, Spinner, statusTone } from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { formatDuration, formatMoney, formatRelative } from "@/lib/format";
import { PROJECT_STATUS, label } from "@/lib/labels";
import { useDeleteProject, useDuplicateProject, useProjects } from "@/lib/queries";

function ProjectCard({ project }: { project: Project }) {
  const duplicate = useDuplicateProject();
  const remove = useDeleteProject();
  const poster = project.sourceVideo?.posterUrl;
  return (
    <div className="group panel overflow-hidden transition-colors hover:border-line-strong">
      <Link href={`/projects/${project.id}`} className="block">
        <div className="checker relative aspect-video overflow-hidden">
          {poster ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={poster} alt="" className="size-full object-cover transition-transform duration-500 group-hover:scale-[1.03]" />
          ) : (
            <div className="flex size-full items-center justify-center text-faint">
              <Film className="size-8" />
            </div>
          )}
          <div className="absolute left-2 top-2 flex gap-1">
            <Badge tone={statusTone(project.status)}>{label(PROJECT_STATUS, project.status)}</Badge>
            {project.isDemo && <Badge tone="info">Exemplo</Badge>}
          </div>
          {project.sourceVideo?.durationSec ? (
            <span className="absolute bottom-2 right-2 rounded bg-black/70 px-1.5 py-0.5 font-mono text-[11px]">
              {formatDuration(project.sourceVideo.durationSec)}
            </span>
          ) : null}
        </div>
        <div className="space-y-1 p-3">
          <p className="truncate text-sm font-medium">{project.name}</p>
          <p className="flex items-center gap-2 text-xs text-muted">
            <span>{project.editCount} alteraç{project.editCount === 1 ? "ão" : "ões"}</span>
            <span>·</span>
            <span>{formatMoney(project.totalCost, project.currency)}</span>
            <span>·</span>
            <span>{formatRelative(project.updatedAt)}</span>
          </p>
        </div>
      </Link>
      <div className="flex justify-end gap-1 border-t border-line px-2 py-1.5 opacity-60 transition-opacity group-hover:opacity-100">
        <Button
          size="sm"
          variant="ghost"
          icon={<Copy className="size-3.5" />}
          disabled={!project.analysis}
          loading={duplicate.isPending}
          onClick={() =>
            duplicate.mutate(project.id, {
              onSuccess: () => toast.ok("Projeto duplicado"),
              onError: (e) => toast.error("Não foi possível duplicar", errorMessage(e)),
            })
          }
        >
          Duplicar
        </Button>
        <Button
          size="sm"
          variant="ghost"
          icon={<Trash2 className="size-3.5" />}
          loading={remove.isPending}
          onClick={() => {
            if (window.confirm(`Excluir "${project.name}" e toda a sua mídia? Esta ação não pode ser desfeita.`)) {
              remove.mutate(project.id, { onSuccess: () => toast.ok("Projeto e mídia excluídos") });
            }
          }}
        >
          Excluir
        </Button>
      </div>
    </div>
  );
}

const STEPS = [
  { title: "Envie um vídeo", text: "Ou use o vídeo de exemplo. Você confirma que tem direito de usá-lo." },
  { title: "A IA separa o vídeo", text: "Cenas, personagens, roupas, objetos e cenário viram itens clicáveis." },
  { title: "Escolha o que mudar", text: "Clique num item e escolha uma opção: \u201ccabelo cacheado\u201d, \u201ccopo \u2192 prato\u201d\u2026" },
  { title: "Revise e gere", text: "Veja o que cada mudança afeta e quanto custa antes de gerar. Depois, compare." },
];

/** Os quatro passos do produto, para quem chega pela primeira vez. */
function HowItWorks() {
  return (
    <section aria-label="Como funciona" className="mb-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {STEPS.map((step, i) => (
        <div key={step.title} className="panel p-4">
          <p className="mb-1 flex items-center gap-2 text-sm font-medium">
            <span className="flex size-6 items-center justify-center rounded-full bg-accent/15 text-xs text-accent">
              {i + 1}
            </span>
            {step.title}
          </p>
          <p className="text-xs leading-relaxed text-muted">{step.text}</p>
        </div>
      ))}
    </section>
  );
}

export default function Home() {
  const { data: projects, isLoading, error } = useProjects();
  return (
    <div className="glow min-h-screen">
      <AppHeader>
        <Link href="/projects/new">
          <Button variant="primary" size="sm" icon={<Plus className="size-4" />}>
            Novo projeto
          </Button>
        </Link>
      </AppHeader>
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
        <section className="mb-10 max-w-2xl">
          <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-line bg-panel px-3 py-1 text-xs text-muted">
            <Sparkles className="size-3.5 text-accent" /> Sistema operacional para remodelagem de vídeo com IA
          </p>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Desmonte o vídeo. <span className="text-gradient">Personalize tudo.</span> Reconstrua.
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-muted">
            O VideoDNA Studio transforma seu vídeo em elementos editáveis — personagens, roupas, objetos,
            cenário — preservando história, ritmo, movimento e câmera. Clique, escolha, visualize e gere.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            <DemoButton />
            <Link href="/projects/new">
              <Button variant="outline" icon={<Upload className="size-4" />}>
                Usar meu vídeo
              </Button>
            </Link>
          </div>
        </section>
        <HowItWorks />
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-muted">Seus projetos</h2>
        </div>
        {isLoading ? (
          <div className="flex justify-center py-20">
            <Spinner className="size-6" />
          </div>
        ) : error ? (
          <EmptyState title="Não foi possível carregar os projetos">{errorMessage(error)}</EmptyState>
        ) : !projects?.length ? (
          <div className="panel">
            <EmptyState icon={<Clapperboard className="size-10" />} title="Nenhum projeto ainda">
              <p className="mb-4 max-w-md">
                Comece pelo exemplo: um vídeo curto já pronto (um menino, um copo e a mãe) para você ver
                o caminho inteiro — análise, edição, plano e resultado — sem precisar enviar nada.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                <DemoButton />
                <Link href="/projects/new">
                  <Button variant="outline" icon={<Plus className="size-4" />}>
                    Enviar meu vídeo
                  </Button>
                </Link>
              </div>
            </EmptyState>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {projects.map((p) => (
              <ProjectCard key={p.id} project={p} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
