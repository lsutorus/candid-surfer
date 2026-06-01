FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy everything first so setuptools can find app/ package
COPY pyproject.toml uv.lock ./
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini alembic.ini
COPY scripts/ scripts/

# Install dependencies (project + deps)
RUN uv sync --no-dev

EXPOSE 8000

# Railway provides PORT env var; default to 8000 for local docker runs
CMD ["sh", "-c", "uv run alembic upgrade head && uv run python scripts/seed.py && uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
