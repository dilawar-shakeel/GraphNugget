FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
WORKDIR /app

# dependencies first for better layer caching
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "--no-sync", "python", "-m", "graphnugget.workflow"]
