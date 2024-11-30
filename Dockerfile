FROM python:3.12-slim-bookworm AS python-base

LABEL Description="DiscordBot"

ENV WORKDIR=/app
ENV USER=discordbot

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
    apt-get install --no-install-recommends -y ca-certificates curl git ssh && \
    python3 -m pip install --upgrade pip && \
    curl -ksSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION"

RUN useradd -ms /bin/bash ${USER}

COPY --chown=${USER}:${USER} config ${WORKDIR}/config
COPY --chown=${USER}:${USER} src ${WORKDIR}/src
COPY --chown=${USER}:${USER} tests ${WORKDIR}/tests
COPY --chown=${USER}:${USER} pyproject.toml ${WORKDIR}
COPY --chown=${USER}:${USER} poetry.lock ${WORKDIR}
COPY --chown=${USER}:${USER} .env ${WORKDIR}

RUN mkdir -p $${LOG_DIRECTORY} && \
    chown -R ${USER}:${USER} $${LOG_DIRECTORY} && \
    chmod -R 755 $${LOG_DIRECTORY}

RUN poetry install --no-interaction --no-ansi --sync && \
    poetry cache clear pypi --all -n

RUN set -ex && \
    apt-get purge curl -y && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

#EXPOSE 5432
USER ${USER}
CMD ["python", "bot.py"]
