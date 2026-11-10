FROM python:3.12-slim

# uv installs the exact versions pinned in uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.6.12 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app.py ./
COPY radar/ ./radar/
COPY static/ ./static/
COPY data/ ./data/
ENV PATH="/app/.venv/bin:$PATH"

# Cloud Run sends traffic to $PORT and needs the server on all interfaces.
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
