FROM --platform=linux/amd64 python:3.11-slim-buster AS python-base

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
    POETRY_VERSION=1.7.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH=/opt/poetry/bin:$PATH

WORKDIR /opt/DiscordBot

RUN set -ex \
    && apt-get update \
    && apt-get install --no-install-recommends -y build-essential curl \
    && curl -sSL https://install.python-poetry.org | python3 - --version "$POETRY_VERSION" \
    && poetry config virtualenvs.create false \
    && apt-get purge --auto-remove -y build-essential

COPY pyproject.toml poetry.lock /opt/DiscordBot/
RUN poetry install --no-interaction --no-ansi --no-dev

COPY src /opt/DiscordBot/src

CMD ["python", "bot.py"]
