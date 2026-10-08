"use client";

import { AppHeader } from "@/components/app-header";
import { Badge, EmptyState, Spinner } from "@/components/ui/primitives";
import { errorMessage } from "@/lib/api";
import { formatMoney, formatPercent } from "@/lib/format";
import { useMetrics, useProviders } from "@/lib/queries";

/** Internal dashboard (spec §61): volume, cost, providers, failures, retries. */
export default function AdminPage() {
  const metrics = useMetrics();
  const providers = useProviders();
  const m = metrics.data;
  return (
    <div className="glow min-h-screen">
      <AppHeader />
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-8 sm:px-6">
        <h1 className="text-2xl font-semibold tracking-tight">Painel interno</h1>
        {metrics.isLoading ? (
          <Spinner className="size-6" />
        ) : metrics.error ? (
          <EmptyState title="Acesso restrito">{errorMessage(metrics.error)}</EmptyState>
        ) : m ? (
          <>
            <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {[
                ["Projetos", m.projects],
                ["Vídeos processados", m.videosProcessed],
                ["Análises", m.analysesCompleted],
                ["Custo total (30d)", formatMoney(m.totalCost, m.currency)],
                ["Tempo médio de geração", m.avgGenerationSec ? `${m.avgGenerationSec}s` : "—"],
                ["Retries / falhas de QA", `${m.retries} / ${m.qaFailures}`],
              ].map(([k, v]) => (
                <div key={String(k)} className="panel p-4">
                  <p className="text-[11px] uppercase tracking-wide text-faint">{k}</p>
                  <p className="mt-1 text-lg font-semibold">{v}</p>
                </div>
              ))}
            </div>
            <section className="panel overflow-x-auto">
              <div className="border-b border-line px-4 py-3 text-sm font-medium">Benchmark de providers (dados próprios)</div>
              <table className="w-full text-left text-xs">
                <thead className="text-faint">
                  <tr>
                    {["Provider", "Capability", "Chamadas", "Sucesso", "Latência média", "Retries", "Custo"].map((h) => (
                      <th key={h} className="px-4 py-2 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {m.providers.map((p) => {
                    const row = p as Record<string, number | string | null>;
                    return (
                      <tr key={`${row.provider}${row.capability}`}>
                        <td className="px-4 py-2 font-mono">{row.provider}</td>
                        <td className="px-4 py-2 text-muted">{row.capability}</td>
                        <td className="px-4 py-2">{row.calls}</td>
                        <td className="px-4 py-2">{formatPercent(Number(row.successRate ?? 0), 1)}</td>
                        <td className="px-4 py-2">{row.avgLatencyMs} ms</td>
                        <td className="px-4 py-2">{row.retries}</td>
                        <td className="px-4 py-2">{formatMoney(Number(row.cost ?? 0), m.currency)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </section>
          </>
        ) : null}
        <section className="panel overflow-x-auto">
          <div className="border-b border-line px-4 py-3 text-sm font-medium">Provider Registry</div>
          <ul className="divide-y divide-line">
            {providers.data?.map((p) => (
              <li key={p.name} className="flex flex-wrap items-center gap-2 px-4 py-2.5 text-xs">
                <span className="w-36 font-mono">{p.name}</span>
                <Badge tone={p.enabled ? "ok" : "neutral"}>{p.enabled ? p.health ?? "on" : "off"}</Badge>
                {p.mock && <Badge tone="warn">mock</Badge>}
                {p.local && <Badge tone="info">local</Badge>}
                <span className="text-muted">{p.capabilities.join(", ")}</span>
                {p.disabledReason && <span className="text-faint">({p.disabledReason})</span>}
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
}
