FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim


COPY . /app
WORKDIR /app

ENV UV_LINK_MODE=copy

RUN uv sync
    
ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

