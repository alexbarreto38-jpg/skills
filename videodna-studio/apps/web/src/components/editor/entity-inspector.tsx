"use client";

import type { DnaEntity, EditHistory, EntityOut, ImpactReport, VideoDNA } from "@videodna/api-client";
import { CircleHelp, Lock, MessageSquarePlus, Plus, Trash2, Undo2, X } from "lucide-react";
import { useMemo, useState } from "react";

import { EntityIcon } from "@/components/editor/entity-icon";
import { ImpactCard } from "@/components/editor/impact-card";
import { SuggestionGrid } from "@/components/editor/suggestion-grid";
import {
  Badge,
  Button,
  ConfidenceBar,
  IconButton,
  Input,
  SectionTitle,
  Textarea,
  cx,
  impactTone,
  importanceTone,
} from "@/components/ui/primitives";
import { toast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/api";
import { useEditor } from "@/lib/editor-store";
import { ENTITY_TYPE, IMPACT, IMPORTANCE, OP_LABEL, QUICK_ACTION, WARDROBE_SLOT, label } from "@/lib/labels";
import { useCorrectEntity, useCreateEdit, useDeleteEdit, usePreviewImpact } from "@/lib/queries";

const HIDDEN_ATTRS = new Set(["tags", "palette", "replacedFrom", "derivedFromLabel"]);

function AttributeList({ entity }: { entity: DnaEntity }) {
  const original = entity.edit?.originalAttributes ?? undefined;
  const attrs = Object.entries(entity.attributes ?? {}).filter(([k]) => !HIDDEN_ATTRS.has(k));
  if (!attrs.length) return null;
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-xs">
      {attrs.map(([k, v]) => {
        const changed = original && JSON.stringify(original[k]) !== JSON.stringify(v);
        const isColor = typeof v === "string" && /^#[0-9a-f]{6}$/i.test(v);
        return (
          <div key={k} className="contents">
            <dt className="text-faint">{k}</dt>
            <dd className={cx("flex items-center gap-1.5 truncate", changed ? "text-[#c9bcff]" : "text-fg/90")}>
              {isColor && <span className="size-3 rounded-sm ring-1 ring-white/20" style={{ background: v as string }} />}
              {typeof v === "object" ? JSON.stringify(v) : String(v)}
              {changed && original?.[k] !== undefined && (
                <span className="truncate text-faint line-through">{String(original[k])}</span>
              )}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}

function UncertaintyCard({ projectId, entity, row }: { projectId: string; entity: DnaEntity; row: EntityOut }) {
  const correct = useCorrectEntity(projectId);
  const options = [entity.label, ...(entity.alternatives ?? []).map((a) => a.label)];
  return (
    <div className="space-y-2 rounded-xl border border-warn/40 bg-warn/10 p-3">
      <p className="flex items-center gap-2 text-sm font-medium text-warn">
        <CircleHelp className="size-4" /> Não tenho certeza sobre este elemento.
      </p>
      <p className="text-xs text-muted">
        Confiança {(entity.confidence * 100).toFixed(0)}%.
        {entity.alternatives?.length ? ` Os modelos discordaram: ${options.join(" / ")}?` : " Confirme ou corrija o rótulo."}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {options.map((option, i) => (
          <Button
            key={option}
            size="sm"
            variant={i === 0 ? "secondary" : "outline"}
            loading={correct.isPending && correct.variables?.value === option}
            onClick={() =>
              correct.mutate(
                { entityId: row.id, property: "label", value: option },
                { onSuccess: () => toast.ok("Análise corrigida", option) },
              )
            }
          >
            {i === 0 ? `É ${option}` : option}
          </Button>
        ))}
      </div>
    </div>
  );
}

function AddObjectForm({ projectId, parent, dna, onDone }: { projectId: string; parent: DnaEntity; dna: VideoDNA; onDone: () => void }) {
  const create = useCreateEdit(projectId);
  const [name, setName] = useState("");
  const [anchor, setAnchor] = useState("");
  const anchors = dna.entities.filter((e) => e.type === "furniture" || (e.type === "environment_part" && e.subtype === "floor"));
  return (
    <div className="space-y-2 rounded-xl border border-line bg-panel-2 p-3">
      <Input placeholder="Ex.: garrafa de água" value={name} onChange={(e) => setName(e.target.value)} />
      <select
        className="h-9 w-full rounded-lg border border-line bg-panel-2 px-2 text-sm"
        value={anchor}
        onChange={(e) => setAnchor(e.target.value)}
      >
        <option value="">Onde? (opcional)</option>
        {anchors.map((a) => (
          <option key={a.id} value={a.id}>
            em cima de {a.label}
          </option>
        ))}
      </select>
      <Button
        size="sm"
        variant="primary"
        className="w-full"
        disabled={!name.trim()}
        loading={create.isPending}
        onClick={() =>
          create.mutate(
            {
              entityKey: parent.id,
              op: "ADD_ENTITY",
              newValue: {
                label: name.trim()[0].toUpperCase() + name.trim().slice(1),
                type: "object",
                placement: anchor ? { relativeTo: anchor, predicate: "on_top_of" } : undefined,
              },
              instruction: `Adicionar ${name.trim()}${anchor ? ` em cima de ${dna.entities.find((e) => e.id === anchor)?.label}` : ""}`,
            },
            {
              onSuccess: () => {
                toast.ok("Elemento adicionado");
                onDone();
              },
              onError: (e) => toast.error("Não foi possível adicionar", errorMessage(e)),
            },
          )
        }
      >
        Adicionar
      </Button>
    </div>
  );
}

export function EntityInspector({
  projectId,
  row,
  entity,
  dna,
  history,
}: {
  projectId: string;
  row: EntityOut;
  entity: DnaEntity;
  dna: VideoDNA;
  history?: EditHistory;
}) {
  const { select, activeCategory, setCategory } = useEditor();
  const create = useCreateEdit(projectId);
  const remove = useDeleteEdit(projectId);
  const previewImpact = usePreviewImpact(projectId);
  const [instruction, setInstruction] = useState("");
  const [removeImpact, setRemoveImpact] = useState<ImpactReport | null>(null);
  const [adding, setAdding] = useState(false);

  const categories = row.categories ?? [];
  const category = activeCategory && categories.some((c) => c.id === activeCategory) ? activeCategory : categories[0]?.id ?? null;
  const activeCat = categories.find((c) => c.id === category);
  const children = useMemo(() => dna.entities.filter((e) => e.parentId === entity.id), [dna, entity.id]);
  const parent = entity.parentId ? dna.entities.find((e) => e.id === entity.parentId) : undefined;
  const edits = (history?.edits ?? []).filter((e) => e.entityKey === entity.id && e.state === "ACTIVE");

  function quick(action: string) {
    if (action === "REPLACE") {
      const target = categories.find((c) => c.op === "REPLACE" || c.op === "APPLY_PRESET");
      if (target) setCategory(target.id);
      return;
    }
    if (action === "CHANGE_APPEARANCE") {
      const target = categories.find((c) => c.op === "CHANGE_APPEARANCE" || c.op === "SET_ATTRIBUTE");
      if (target) setCategory(target.id);
      return;
    }
    if (action === "APPLY_PRESET") {
      setCategory("environment_preset");
      return;
    }
    if (action === "ADD_ENTITY") {
      setAdding(true);
      return;
    }
    if (action === "REMOVE") {
      previewImpact.mutate({ entityKey: entity.id, op: "REMOVE" }, { onSuccess: setRemoveImpact });
      return;
    }
    if (action === "KEEP") {
      create.mutate(
        { entityKey: entity.id, op: "KEEP" },
        { onSuccess: () => toast.ok("Elemento travado", `${entity.label} será mantido exatamente como está.`) },
      );
    }
  }

  return (
    <div className="space-y-5 p-4">
      <header className="space-y-2">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="flex items-center gap-1.5 text-[11px] uppercase tracking-wide text-faint">
              <EntityIcon type={entity.type} subtype={entity.subtype} className="size-3" />
              {entity.type === "wardrobe" ? label(WARDROBE_SLOT, entity.subtype) : label(ENTITY_TYPE, entity.type)}
              {parent && <span className="normal-case tracking-normal"> · {parent.label}</span>}
            </p>
            <h2 className="mt-0.5 truncate text-lg font-semibold tracking-tight">{entity.label}</h2>
          </div>
          <IconButton label="Fechar" onClick={() => select(null)}>
            <X className="size-4" />
          </IconButton>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge tone={importanceTone(entity.importance)}>{label(IMPORTANCE, entity.importance)}</Badge>
          {entity.edit?.modified && <Badge tone="accent">Modificado</Badge>}
          {entity.edit?.locked && (
            <Badge tone="info">
              <Lock className="size-3" /> Mantido
            </Badge>
          )}
          {entity.edit?.removed && <Badge tone="bad">Removido</Badge>}
          <span className="flex-1" />
          <ConfidenceBar value={entity.confidence} />
        </div>
        {entity.description && <p className="text-xs leading-relaxed text-muted">{entity.description}</p>}
      </header>

      {entity.needsReview && <UncertaintyCard projectId={projectId} entity={entity} row={row} />}

      {children.length > 0 && (
        <section>
          <SectionTitle>{entity.type === "character" ? "Aparência" : "Elementos"}</SectionTitle>
          <div className="grid grid-cols-2 gap-1.5">
            {children.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => select(c.id)}
                className="flex items-center gap-2 rounded-lg border border-line bg-panel-2 px-2.5 py-2 text-left hover:border-line-strong"
              >
                <span className="text-muted">
                  <EntityIcon type={c.type} subtype={c.subtype} />
                </span>
                <span className="min-w-0">
                  <span className="block text-[10px] uppercase tracking-wide text-faint">
                    {c.type === "wardrobe" ? label(WARDROBE_SLOT, c.subtype) : label(ENTITY_TYPE, c.type)}
                  </span>
                  <span className="block truncate text-xs">{c.label}</span>
                </span>
                {c.edit?.modified && <span className="ml-auto size-1.5 shrink-0 rounded-full bg-accent" />}
              </button>
            ))}
          </div>
        </section>
      )}

      {(row.quickActions?.length ?? 0) > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {row.quickActions!.map((a) => (
            <Button key={a} size="sm" variant={a === "REMOVE" ? "danger" : "outline"} onClick={() => quick(a)} loading={a === "REMOVE" && previewImpact.isPending}>
              {label(QUICK_ACTION, a)}
            </Button>
          ))}
        </div>
      )}

      {removeImpact && (
        <div className="space-y-2">
          <ImpactCard impact={removeImpact} />
          <div className="flex gap-2">
            <Button size="sm" variant="ghost" className="flex-1" onClick={() => setRemoveImpact(null)}>
              Cancelar
            </Button>
            <Button
              size="sm"
              variant="danger"
              className="flex-1"
              disabled={removeImpact.warnings?.some((w) => w.blocking)}
              loading={create.isPending}
              onClick={() =>
                create.mutate(
                  { entityKey: entity.id, op: "REMOVE" },
                  {
                    onSuccess: () => {
                      toast.ok("Elemento removido");
                      setRemoveImpact(null);
                    },
                    onError: (e) => toast.error("Não foi possível remover", errorMessage(e)),
                  },
                )
              }
            >
              Remover
            </Button>
          </div>
        </div>
      )}

      {adding && <AddObjectForm projectId={projectId} parent={entity} dna={dna} onDone={() => setAdding(false)} />}

      {categories.length > 0 && category && activeCat && (
        <section className="space-y-3">
          <div className="flex flex-wrap gap-1">
            {categories.map((c) => (
              <button
                key={c.id}
                type="button"
                onClick={() => setCategory(c.id)}
                className={cx(
                  "rounded-full px-3 py-1 text-xs font-medium transition-colors",
                  c.id === category ? "bg-fg text-bg" : "bg-panel-3 text-muted hover:text-fg",
                )}
              >
                {c.label}
              </button>
            ))}
          </div>
          <SuggestionGrid
            key={`${row.id}:${category}`}
            projectId={projectId}
            entity={row}
            category={category}
            display={activeCat.display ?? "cards"}
            instruction={instruction}
          />
        </section>
      )}

      <section className="space-y-2">
        <SectionTitle>Instrução personalizada</SectionTitle>
        <Textarea
          rows={2}
          placeholder={
            entity.type === "environment_part" && entity.subtype === "window_view"
              ? "Quero que pela janela apareça uma praia."
              : entity.type === "wardrobe"
                ? "Quero que essa camiseta seja amarela."
                : "Descreva a alteração com suas palavras…"
          }
          value={instruction}
          onChange={(e) => setInstruction(e.target.value)}
        />
        <div className="flex items-center justify-between gap-2">
          <p className="text-[11px] text-faint">Complementa a opção escolhida acima — ou aplique sozinha.</p>
          <Button
            size="sm"
            variant="secondary"
            icon={<MessageSquarePlus className="size-3.5" />}
            disabled={!instruction.trim()}
            loading={create.isPending}
            onClick={() =>
              create.mutate(
                { entityKey: entity.id, op: "INSTRUCTION", instruction: instruction.trim() },
                {
                  onSuccess: () => {
                    toast.ok("Instrução adicionada");
                    setInstruction("");
                  },
                  onError: (e) => toast.error("Instrução inválida", errorMessage(e)),
                },
              )
            }
          >
            Aplicar instrução
          </Button>
        </div>
      </section>

      {edits.length > 0 && (
        <section>
          <SectionTitle>Alterações neste elemento</SectionTitle>
          <ul className="space-y-1.5">
            {edits.map((e) => {
              const impact = e.impact as { level?: string } | undefined;
              return (
                <li key={e.id} className="flex items-center gap-2 rounded-lg bg-panel-2 px-2.5 py-2 text-xs">
                  <Badge tone={impactTone(impact?.level)}>{label(IMPACT, impact?.level).replace("Impacto ", "")}</Badge>
                  <span className="min-w-0 flex-1 truncate">
                    {label(OP_LABEL, e.op)}
                    {e.property ? ` · ${e.property}` : ""}
                    {e.instruction ? ` · “${e.instruction}”` : ""}
                  </span>
                  <IconButton label="Remover alteração" onClick={() => remove.mutate(e.id)}>
                    <Trash2 className="size-3.5" />
                  </IconButton>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <section>
        <SectionTitle>Atributos detectados</SectionTitle>
        <AttributeList entity={entity} />
        <p className="mt-3 flex flex-wrap gap-1 text-[10px] text-faint">
          Fontes: {(entity.sources ?? []).join(", ") || "—"} · {entity.appearances?.length ?? 0} aparição(ões)
          {entity.edit?.originalLabel && entity.edit.originalLabel !== entity.label && (
            <span className="flex items-center gap-1">
              · <Undo2 className="size-3" /> original: {entity.edit.originalLabel}
            </span>
          )}
        </p>
      </section>

      {entity.type === "environment" && !adding && (
        <Button size="sm" variant="ghost" icon={<Plus className="size-3.5" />} onClick={() => setAdding(true)}>
          Adicionar objeto ao cenário
        </Button>
      )}
    </div>
  );
}
