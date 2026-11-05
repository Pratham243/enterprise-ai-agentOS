# =============================================================================
# Enterprise AI AgentOS — Production Dockerfile
# =============================================================================
# Multi-stage build: small final image, no dev tools or cache in production.
#
# Build:  docker build -t agentos .
# Run:    docker run -p 8000:8000 --env-file .env agentos
# =============================================================================

# --- Stage 1: Builder --------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: Runtime --------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ backend/
COPY pyproject.toml .

# Create a non-root user for security
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Health check for container orchestrators
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
