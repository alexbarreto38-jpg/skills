# MinIO for local development, built from source.
#
# MinIO stopped publishing community container images, and its docs now point
# community users to source builds. Pin the module version below (a Go
# pseudo-version from `curl https://proxy.golang.org/github.com/minio/minio/@latest`)
# and bump it deliberately. Production uses AWS S3 / Cloudflare R2 instead.
# Behind a TLS-intercepting proxy: `--secret id=ca,src=/path/to/proxy-ca.pem`.

FROM golang:1.25-bookworm AS build
ARG MINIO_VERSION=v0.0.0-20260212201848-7aac2a2c5b7c
ENV CGO_ENABLED=0 GOFLAGS=-trimpath
RUN --mount=type=secret,id=ca,required=false \
    --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    set -eu; \
    if [ -s /run/secrets/ca ]; then \
      cat /etc/ssl/certs/ca-certificates.crt /run/secrets/ca > /tmp/ca.pem; \
      export SSL_CERT_FILE=/tmp/ca.pem; \
    fi; \
    go install -ldflags "-s -w" github.com/minio/minio@${MINIO_VERSION}; \
    mkdir -p /out/data

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /go/bin/minio /usr/local/bin/minio
# Owned by the distroless "nonroot" user so a fresh named volume is writable.
COPY --from=build --chown=65532:65532 /out/data /data
EXPOSE 9000 9001
ENTRYPOINT ["/usr/local/bin/minio"]
CMD ["server", "/data", "--console-address", ":9001"]
