FROM python:3.13-slim-bookworm AS python-base

LABEL Description="DiscordBot"

ARG LOG_DIRECTORY="/app/logs"
ENV LOG_DIRECTORY="${LOG_DIRECTORY}"

ENV WORKDIR=/app

ENV TERM=xterm \
    TZ="UTC" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_ROOT_USER_ACTION=ignore \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=1.8.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONPATH="$PYTHONPATH:${WORKDIR}/src" \
    PATH=/opt/poetry/bin:$PATH

WORKDIR ${WORKDIR}

RUN set -ex && \
    apt-get update && \
    apt-get install --no-install-recommends -y ca-certificates curl && \
    python3 -m pip install --upgrade pip && \
    curl -sSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION" && \
    apt-get purge curl -y && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY config ${WORKDIR}/config
COPY src ${WORKDIR}/src
COPY tests ${WORKDIR}/tests
COPY bot.py ${WORKDIR}
COPY pyproject.toml ${WORKDIR}
COPY poetry.lock ${WORKDIR}
COPY .env ${WORKDIR}

RUN mkdir -p ${LOG_DIRECTORY} && \
    poetry install --no-interaction --no-ansi --sync && \
    poetry cache clear pypi --all -n
