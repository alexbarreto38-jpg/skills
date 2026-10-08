# 0009 — MinIO compilado do código-fonte para desenvolvimento

- **Status:** Aceito — ajustado pelo [ADR-0013](0013-local-storage-default-stack.md): o MinIO saiu do stack padrão e sobe com `docker-compose.s3.yml`
- **Data:** 2026-10-08

## Contexto

O ambiente local precisa de um storage S3-compatível para exercitar upload multipart com
URLs assinadas, CORS e ETag exatamente como em produção (S3/R2). O MinIO deixou de
publicar imagens de container para a comunidade; o repositório no Docker Hub não oferece
mais as tags, e o registro alternativo não é acessível sem autenticação.

## Decisão

`infra/minio/Dockerfile` compila o servidor com `go install` numa versão fixada
(pseudo-versão Go de um commit específico) e copia o binário estático para uma imagem
distroless `nonroot`, com `/data` pertencente ao usuário não-root para que um volume novo
seja gravável. O compose usa essa imagem (`videodna/minio:local`). A atualização é
deliberada: trocar `MINIO_VERSION`.

## Alternativas consideradas

- **Imagem de terceiros republicando o MinIO** — cadeia de suprimentos não verificável.
- **Outro servidor S3-compatível** — possível, mas o MinIO é o mais próximo do
  comportamento do S3 em multipart, presign e CORS, que é o que queremos testar.
- **Storage local também no compose** — deixaria o caminho S3 (presign, multipart direto do
  navegador) sem teste de integração.

## Consequências

- O primeiro build compila o MinIO (alguns minutos; depois fica em cache).
- Em produção não há MinIO: AWS S3 ou Cloudflare R2, mudando só as variáveis `S3_*`.
- Atrás de proxy com interceptação TLS, o build usa o mesmo secret opcional `ca` dos outros
  Dockerfiles.
