FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

ENV UV_LINK_MODE=copy
RUN uv sync

ENV PATH="/app/.venv/bin:$PATH"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
