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
    && apt-get install --no-install-recommends -y build-essential curl \
    && curl -sSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION" \
    && poetry config virtualenvs.create false \
    && apt-get purge --auto-remove -y build-essential \
    && apt-get autoremove -y \
    && apt-get clean

RUN useradd -ms /bin/bash discordbot

COPY --chown=discordbot:discordbot pyproject.toml poetry.lock .env /opt/DiscordBot/
RUN poetry install --no-interaction --no-ansi $(test "$CONFIG_ENV" == prod && echo "--no-dev")

USER discordbot
EXPOSE 5432

CMD ["python", "bot.py"]
