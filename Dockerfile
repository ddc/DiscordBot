FROM python:3.14.3-alpine3.23 AS python-base

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
    PYTHONPATH="$PYTHONPATH:${WORKDIR}/src" \
    PATH="/home/botuser/.local/bin:$PATH"

WORKDIR ${WORKDIR}

RUN set -ex && \
    apk add --no-cache ca-certificates curl && \
    curl --proto '=https' -LsSf https://astral.sh/uv/install.sh | sh && \
    addgroup -g 1000 botuser && \
    adduser -u 1000 -G botuser -h /home/botuser -D botuser && \
    mv /root/.local /home/botuser/.local && \
    chown -R botuser:botuser /home/botuser/.local

FROM python-base AS final

COPY --chmod=555 alembic.ini ${WORKDIR}
COPY --chmod=555 src ${WORKDIR}/src
COPY --chmod=555 tests ${WORKDIR}/tests
COPY --chmod=555 pyproject.toml ${WORKDIR}
COPY --chmod=555 uv.lock ${WORKDIR}
COPY --chmod=555 .env ${WORKDIR}

RUN set -ex && \
    mkdir -p ${LOG_DIRECTORY} && \
    uv sync --frozen --no-dev && \
    uv cache clean && \
    chown -R botuser:botuser ${WORKDIR}

USER botuser
