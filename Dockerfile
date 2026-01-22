FROM python:3.14-slim-bookworm AS python-base

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
    PYTHONPATH="$PYTHONPATH:${WORKDIR}/src" \
    PATH="/root/.local/bin:$PATH"

WORKDIR ${WORKDIR}

RUN set -ex && \
    apt-get update && \
    apt-get install --no-install-recommends -y ca-certificates curl && \
    curl --proto '=https' -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/cache/apt/archives /var/lib/apt/lists/*

COPY config ${WORKDIR}/config
COPY src ${WORKDIR}/src
COPY tests ${WORKDIR}/tests
COPY bot.py ${WORKDIR}
COPY pyproject.toml ${WORKDIR}
COPY uv.lock ${WORKDIR}
COPY .env ${WORKDIR}

RUN mkdir -p ${LOG_DIRECTORY} && \
    uv sync --no-dev && \
    uv cache clean
