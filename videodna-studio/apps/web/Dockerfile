# VideoDNA web (Next.js standalone). Build context: the monorepo root
# (`videodna-studio/`), because the app depends on packages/api-client.
# Behind a TLS-intercepting proxy: `--secret id=ca,src=/path/to/proxy-ca.pem`.

FROM node:22-bookworm-slim AS build
WORKDIR /repo
COPY pnpm-workspace.yaml package.json pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY packages/api-client/package.json packages/api-client/package.json
RUN --mount=type=secret,id=ca,required=false \
    --mount=type=cache,target=/root/.local/share/pnpm/store \
    set -eu; \
    if [ -s /run/secrets/ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/ca; fi; \
    npm install -g pnpm@10.28.0 --no-fund --no-audit; \
    pnpm install --frozen-lockfile --filter @videodna/web...

COPY packages/api-client packages/api-client
COPY apps/web apps/web
# The API URL is inlined at build time (it is what the *browser* calls).
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_TELEMETRY_DISABLED=1
RUN pnpm --filter @videodna/web build

FROM node:22-bookworm-slim AS runtime
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
RUN useradd --create-home --uid 10001 web
COPY --from=build --chown=web /repo/apps/web/.next/standalone ./
COPY --from=build --chown=web /repo/apps/web/.next/static ./apps/web/.next/static
COPY --from=build --chown=web /repo/apps/web/public ./apps/web/public
USER web
EXPOSE 3000
CMD ["node", "apps/web/server.js"]
