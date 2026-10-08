# VideoDNA backend image — used by both the `api` and the `worker` services.
#
# No apt-get: FFmpeg comes from a static-build image, and Python deps from the
# uv lockfile. Behind a TLS-intercepting proxy, pass its CA as a build secret:
#   docker build --secret id=ca,src=/path/to/proxy-ca.pem apps/api
# (an absent or empty secret is ignored).

FROM mwader/static-ffmpeg:7.1 AS ffmpeg

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# FFmpeg/FFprobe do every deterministic media step (probe, proxy, shots, keyframes, QA).
COPY --from=ffmpeg /ffmpeg /ffprobe /usr/local/bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./

# Dependencies first (cached layer), then the project itself.
RUN --mount=type=secret,id=ca,required=false \
    --mount=type=cache,target=/root/.cache \
    set -eu; \
    if [ -s /run/secrets/ca ]; then \
      cat /etc/ssl/certs/ca-certificates.crt /run/secrets/ca > /tmp/ca.pem; \
      export SSL_CERT_FILE=/tmp/ca.pem PIP_CERT=/tmp/ca.pem; \
    fi; \
    pip install --no-cache-dir uv==0.11.32; \
    uv sync --frozen --no-dev --no-install-project; \
    rm -f /tmp/ca.pem

COPY src ./src
COPY config ./config
COPY migrations ./migrations
COPY alembic.ini ./
RUN --mount=type=secret,id=ca,required=false \
    --mount=type=cache,target=/root/.cache \
    set -eu; \
    if [ -s /run/secrets/ca ]; then \
      cat /etc/ssl/certs/ca-certificates.crt /run/secrets/ca > /tmp/ca.pem; \
      export SSL_CERT_FILE=/tmp/ca.pem; \
    fi; \
    uv sync --frozen --no-dev; \
    rm -f /tmp/ca.pem

RUN useradd --create-home --uid 10001 videodna \
    && mkdir -p /data/storage /data/work \
    && chown -R videodna /data
USER videodna

ENV STORAGE_LOCAL_ROOT=/data/storage \
    WORK_DIR=/data/work \
    PROVIDERS_CONFIG_PATH=/app/config/providers.yaml \
    FEATURES_CONFIG_PATH=/app/config/features.yaml

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4).status == 200 else 1)"

CMD ["sh", "-c", "alembic upgrade head && uvicorn videodna.main:app --host 0.0.0.0 --port 8000 --proxy-headers"]
