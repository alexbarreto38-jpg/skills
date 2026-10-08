# 0012 — Análise em camadas: local primeiro, IA só no necessário

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

Analisar cada frame com um modelo multimodal seria caro e lento, e boa parte da estrutura
de um vídeo (metadados, cortes, cores, quadros representativos) é obtida com
processamento determinístico.

## Decisão

A análise roda em camadas (`services/analysis/pipeline.py`):

1. **Local, sem custo:** ffprobe, hash, proxy 720p, poster, detecção de shots (scene score
   por frame + blackdetect, num único passe do FFmpeg, com detector de picos adaptativo),
   keyframes por shot (início/meio/fim + intervalo, com teto) e cores dominantes.
2. **IA, só sobre o que a camada local produziu:** narrativa multimodal sobre o proxy;
   detecção e OCR **só nos keyframes**; tracking por shot; fala e áudio.
3. **Local de novo:** montagem do DNA — consenso entre detector e modelo multimodal,
   confiança, IDs persistentes, elementos incertos marcados para revisão.

Mesmo conteúdo (hash) + mesma versão de pipeline + mesmo modo + mesmos cortes ⇒ as camadas
de IA são reaproveitadas de uma análise anterior do mesmo usuário, sem custo.

## Alternativas consideradas

- **Um único modelo multimodal sobre o vídeo inteiro** — mais simples, mas sem cortes
  precisos, sem bboxes por frame e sem como verificar o que o modelo afirmou.
- **Detecção em todos os frames** — custo proporcional à duração × fps, sem ganho para o
  editor, que trabalha por shot e por keyframe.
- **Limiar fixo de scene score** — perde cortes entre planos de luminância parecida
  (acontecia no vídeo de teste: 1 de 5 cortes detectado).

## Consequências

- O custo de análise cresce com o número de shots e keyframes, não com a duração em frames.
- Os cortes detectados localmente são a espinha do DNA: shots, keyframes, tracks e o plano
  de geração se alinham a eles.
- Segmentação (máscaras) fica sob demanda, na geração, quando uma edição localizada
  precisa dela — não na análise.
