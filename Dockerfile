# syntax=docker/dockerfile:1

# ---- builder stage (install deps with uv) ----
FROM ghcr.io/astral-sh/uv:python3.13-slim AS builder

WORKDIR /app

# Copy project metadata and install Python deps
COPY pyproject.toml ./
RUN uv venv .venv && \
    UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --no-dev

# Copy application code + model
COPY app/ ./app/

# ---- runtime stage ----
FROM python:3.13-slim

WORKDIR /app

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app

# Ensure the virtualenv python is on PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run as non-root user
RUN useradd --create-home --uid 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
