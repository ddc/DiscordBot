FROM python:3.12-slim-bookworm AS python-base

LABEL Description="DiscordBot"

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
    POETRY_VERSION=1.8.3 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH=/opt/poetry/bin:$PATH

WORKDIR /opt/DiscordBot
RUN mkdir -p /opt/DiscordBot/logs

RUN set -ex \
    && apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && curl -sSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION" \
    && apt-get autoremove -y \
    && apt-get clean

RUN useradd -ms /bin/bash discordbot

COPY --chown=discordbot:discordbot pyproject.toml poetry.lock .env /opt/DiscordBot/
RUN poetry install --no-interaction --no-ansi --sync $(if [ "$CONFIG_ENV" = 'prod' ]; then echo '--only main'; fi)

EXPOSE 5432
USER discordbot
CMD ["python", "bot.py"]
