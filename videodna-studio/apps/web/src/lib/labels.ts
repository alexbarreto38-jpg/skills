/** pt-BR labels for backend enums. Unknown values fall back to the raw value. */

export const ENTITY_TYPE: Record<string, string> = {
  character: "Personagem",
  hair: "Cabelo",
  wardrobe: "Roupa",
  accessory: "Acessório",
  object: "Objeto",
  furniture: "Móvel",
  environment: "Ambiente",
  environment_part: "Parte do cenário",
  lighting: "Iluminação",
  text: "Texto",
  audio: "Áudio",
};

export const WARDROBE_SLOT: Record<string, string> = {
  upper: "Roupa superior",
  lower: "Roupa inferior",
  footwear: "Calçado",
  full: "Look completo",
};

export const IMPORTANCE: Record<string, string> = {
  ESSENTIAL: "Essencial",
  IMPORTANT: "Importante",
  DECORATIVE: "Decorativo",
};

export const IMPACT: Record<string, string> = {
  NONE: "Sem impacto",
  LOW: "Impacto baixo",
  MEDIUM: "Impacto médio",
  HIGH: "Impacto alto",
};

export const QUALITY_MODE: Record<string, { label: string; hint: string }> = {
  ECONOMY: { label: "Econômico", hint: "Prioriza custo" },
  BALANCED: { label: "Equilibrado", hint: "Melhor relação qualidade/custo" },
  MAX: { label: "Qualidade máxima", hint: "Modelos mais fortes, mais tentativas" },
};

export const STRATEGY: Record<string, string> = {
  PASSTHROUGH: "Sem alteração",
  ATTRIBUTE_EDIT: "Edição de atributo",
  LOCALIZED_EDIT: "Edição localizada",
  BACKGROUND_REPLACEMENT: "Troca de cenário",
  SHOT_RECONSTRUCTION: "Reconstrução do shot",
  FULL_REGENERATION: "Regeneração completa",
};

export const DEPENDENCY: Record<string, string> = {
  HAND_INTERACTION: "Interação com a mão",
  PHYSICS_MOTION: "Física / movimento",
  DESTRUCTION_FX: "Quebra / fragmentos",
  CONTACT_SURFACE: "Contato com superfície",
  GAZE_TARGET: "Direção do olhar",
  OCCLUSION: "Oclusão",
  CONTINUITY: "Continuidade entre shots",
  DERIVED_ENTITY: "Elemento derivado",
  LIGHTING: "Iluminação",
  STORY_ROLE: "Papel na história",
  AUDIO_SFX: "Efeito sonoro",
  CHILD_ELEMENTS: "Elementos do cenário",
};

export const PROJECT_STATUS: Record<string, string> = {
  DRAFT: "Rascunho",
  UPLOADING: "Enviando",
  UPLOADED: "Enviado",
  ANALYZING: "Analisando",
  READY: "Pronto para editar",
  GENERATING: "Gerando",
  COMPLETED: "Concluído",
  FAILED: "Falhou",
};

export const JOB_STATUS: Record<string, string> = {
  QUEUED: "Na fila",
  PREPARING: "Preparando",
  ANALYZING: "Analisando",
  GENERATING: "Gerando",
  QA: "Verificando qualidade",
  REPAIRING: "Corrigindo",
  ASSEMBLING: "Montando",
  COMPLETED: "Concluído",
  FAILED: "Falhou",
  CANCELLED: "Cancelado",
};

export const OP_LABEL: Record<string, string> = {
  SET_ATTRIBUTE: "Alterar",
  CHANGE_APPEARANCE: "Alterar aparência",
  REPLACE: "Substituir",
  REMOVE: "Remover",
  KEEP: "Manter",
  APPLY_PRESET: "Aplicar estilo",
  ADD_ENTITY: "Adicionar",
  CORRECT: "Corrigir análise",
  INSTRUCTION: "Instrução",
};

export const QUICK_ACTION: Record<string, string> = {
  KEEP: "Manter",
  REPLACE: "Substituir",
  REMOVE: "Remover",
  CHANGE_APPEARANCE: "Alterar aparência",
  APPLY_PRESET: "Trocar estilo",
  ADD_ENTITY: "Adicionar objeto",
};

/** Analysis pipeline stages in the order the worker reports them. */
export const ANALYSIS_STAGES: { id: string; label: string }[] = [
  { id: "ingest", label: "Recebendo o vídeo" },
  { id: "probe", label: "Metadados técnicos" },
  { id: "proxy", label: "Proxy 720p" },
  { id: "shots", label: "Cortes e shots" },
  { id: "keyframes", label: "Keyframes" },
  { id: "narrative", label: "História e personagens" },
  { id: "detection", label: "Objetos e textos" },
  { id: "tracking", label: "Rastreamento" },
  { id: "audio", label: "Áudio" },
  { id: "assembly", label: "Video DNA" },
];

export const GENERATION_STAGES: { id: string; label: string }[] = [
  { id: "prepare", label: "Preparando mídia" },
  { id: "references", label: "Reference packs" },
  { id: "generate", label: "Gerando shots" },
  { id: "qa", label: "Controle de qualidade" },
  { id: "repair", label: "Reparo localizado" },
  { id: "assemble", label: "Montagem final" },
];

/** Why a video was refused, and what to do about it (by the error code stored on the source video). */
export const REJECT_REASON: Record<string, string> = {
  VIDEO_TOO_LONG: "O vídeo passa do limite de duração. Corte um trecho menor e envie de novo.",
  UNSUPPORTED_MEDIA: "Este formato não é aceito. Envie um vídeo MP4, MOV, WebM ou MKV.",
  INVALID_VIDEO: "Não conseguimos abrir este arquivo como vídeo. Ele pode estar corrompido — tente exportá-lo de novo.",
  FILE_TOO_LARGE: "O arquivo é grande demais. Envie uma versão menor (ou mais curta) do vídeo.",
};

export function label(map: Record<string, string>, key: string | null | undefined): string {
  if (!key) return "";
  return map[key] ?? key;
}
