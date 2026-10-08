# 0010 — Storage abstrato, upload direto com URLs assinadas

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

Vídeos de referência podem ter gigabytes. Passar o arquivo pela API ocuparia workers web e
banda à toa, e conexões caem no meio de uploads grandes. Em desenvolvimento, exigir S3
seria um obstáculo; em produção, o storage é S3 ou R2.

## Decisão

- Uma interface única (`storage/base.py`): `put_file`/`put_bytes`, `download`, `copy`,
  `delete`/`delete_prefix`, `list_keys`, `signed_get_url` e multipart
  (`create_multipart`, `signed_part_url`, `list_parts`, `complete_multipart`,
  `abort_multipart`).
- **S3** (`storage/s3.py`, boto3): presign nativo; upload multipart **direto do navegador**
  para o bucket, uma URL assinada por parte; o navegador lê o `ETag` de cada parte (CORS
  expõe o header).
- **Local** (`storage/local.py`): arquivos em disco; as URLs são tokens HMAC com expiração
  servidos pela própria API (`/media/{token}`), com suporte a `Range`.
- Upload **retomável**: `GET /uploads/{id}` informa as partes já recebidas; o cliente envia
  só as que faltam.
- `S3_ENDPOINT_URL` (servidor) e `S3_PUBLIC_ENDPOINT_URL` (o que vai nas URLs assinadas)
  são separados, porque dentro do compose o MinIO não tem o mesmo nome que o navegador vê.

## Alternativas consideradas

- **Upload pela API (streaming)** — simples, mas a API vira gargalo de banda.
- **Bucket público** — inaceitável para vídeos de usuários.
- **tus/resumable próprio** — o multipart do S3 já é retomável e é o que o storage de
  produção oferece.

## Consequências

- A API só assina e valida; os bytes vão direto para o storage.
- O conteúdo é revalidado por ffprobe depois do upload — o que o cliente declarou no
  início não é confiável.
- Existe também um upload simples (`POST /projects/{id}/upload`) para scripts e
  ferramentas que não querem fazer multipart.
