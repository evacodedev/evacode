FROM python:3.11-slim-bookworm AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.2.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

FROM python-base AS builder
LABEL stage="builder"
RUN apt-get update && \
    apt-get install --no-install-recommends -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*


RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH

COPY poetry.lock pyproject.toml ./


RUN poetry install --no-root

FROM python-base AS development
WORKDIR $PYSETUP_PATH
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH
COPY src /evacode-api/
WORKDIR /evacode-api
EXPOSE 8000
