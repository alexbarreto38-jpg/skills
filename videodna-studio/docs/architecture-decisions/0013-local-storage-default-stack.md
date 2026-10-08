# 0013 — Stack padrão com storage local; MinIO opcional

- **Status:** Aceito (ajusta o ADR-0009)
- **Data:** 2026-10-08

## Contexto

O primeiro uso real foi num Windows com Docker Desktop e rede instável. O
`docker compose up --build` resolvia as imagens base de quatro serviços ao mesmo tempo,
estourava o prazo do registry (`DeadlineExceeded`) e não criava nenhum container. O MinIO,
compilado do código-fonte (ADR-0009), era o build mais pesado e o que mais dependia de rede
(módulos Go), sem ser necessário para usar o produto: o storage local já cobre upload
retomável, URLs assinadas e `Range`.

## Decisão

- O `docker-compose.yml` padrão usa `STORAGE_BACKEND=local` com um volume `storage`
  compartilhado entre `api` e `worker`. Só duas imagens são construídas (API e web).
- O MinIO e o caminho S3 ficam em `docker-compose.s3.yml`, combinado com `-f` quando se quer
  testar o fluxo de produção (upload direto do navegador para o bucket).
- Postgres e Redis deixam de publicar portas no host por padrão (colidiam com instalações
  locais); `docker-compose.dev.yml` as publica para o desenvolvimento fora de containers.
- Os Dockerfiles não declaram mais `# syntax=docker/dockerfile:1.7`: o frontend embutido do
  BuildKit já suporta `RUN --mount`, e a linha obrigava um download extra do Docker Hub.
- No Windows, `iniciar.ps1` baixa as imagens base uma de cada vez com novas tentativas,
  constrói com `docker build` (sem o bake paralelo do compose), sobe com `--no-build`, espera
  a API e o site responderem e abre o navegador. As imagens levam a revisão do Git como
  label e são reconstruídas sozinhas depois de um `git pull`.

## Alternativas consideradas

- **Manter o MinIO no padrão e só documentar o `docker pull` prévio** — continua exigindo
  compilar Go no primeiro uso, o passo mais lento e mais sujeito a falhas de rede.
- **Publicar imagens prontas num registry** — elimina todo build local; fica como próximo
  passo, porque exige um pipeline de publicação e decidir onde hospedar as imagens.

## Consequências

- Primeiro uso mais rápido e com menos pontos de falha; o caminho S3 continua testado pela
  suíte (moto) e disponível com um `-f` a mais.
- Quem usava `docker compose up` com MinIO precisa acrescentar `-f docker-compose.s3.yml`;
  os dados já enviados ao volume do MinIO não migram sozinhos para o volume `storage`.
