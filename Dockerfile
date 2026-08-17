# ---------------------------------------------------------------------------
# Build stage: resolves the virtualenv. Only .venv reaches the final image
# ---------------------------------------------------------------------------
FROM python:3.14.7-alpine3.24 AS python-base

LABEL Description="DiscordBot"

ENV WORKDIR=/app \
    TZ="UTC" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR ${WORKDIR}

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN apk upgrade --no-cache && apk add --no-cache ca-certificates

COPY pyproject.toml uv.lock ${WORKDIR}/

RUN set -ex && \
    uv sync --frozen --no-dev --no-build && \
    uv cache clean

# ---------------------------------------------------------------------------
# Final stage: clean base
# ---------------------------------------------------------------------------
FROM python:3.14.7-alpine3.24 AS final

LABEL Description="DiscordBot"

ARG LOG_DIRECTORY="/app/logs"

ENV LOG_DIRECTORY="${LOG_DIRECTORY}" \
    WORKDIR=/app \
    TERM=xterm \
    TZ="UTC" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/tmp/uv-cache \
    PYTHONPATH="$PYTHONPATH:/app/src"

WORKDIR ${WORKDIR}

RUN apk upgrade --no-cache && apk add --no-cache ca-certificates

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
COPY --from=python-base --chown=65534:65534 ${WORKDIR}/.venv ${WORKDIR}/.venv
COPY --chmod=555 alembic.ini ${WORKDIR}
COPY --chmod=555 src ${WORKDIR}/src
COPY --chmod=555 tests ${WORKDIR}/tests
COPY --chmod=555 pyproject.toml ${WORKDIR}
COPY --chmod=555 uv.lock ${WORKDIR}
COPY --chmod=555 .env ${WORKDIR}

RUN set -ex && \
    ${WORKDIR}/.venv/bin/python -c "import discord, sqlalchemy, psycopg, asyncpg; print('venv OK')" && \
    mkdir -p "${LOG_DIRECTORY}" && \
    chown -R 65534:65534 "${LOG_DIRECTORY}"

# 65534:65534 is nobody:nobody in alpine. Numeric so the host can resolve it (DL3066)
USER 65534:65534
