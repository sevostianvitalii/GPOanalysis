# =============================================================================
# GPO Analysis Tool - Multi-Stage Dockerfile
# Compatible with Docker and Podman on Windows, Mac, and Linux
# =============================================================================

# Allow overriding base images for cases where docker.io is blocked
ARG BASE_NODE_IMAGE=node:20-alpine
ARG BASE_PYTHON_IMAGE=python:3.12-slim

# -----------------------------------------------------------------------------
# Stage 1: Build Frontend
# -----------------------------------------------------------------------------
FROM ${BASE_NODE_IMAGE} AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better caching
COPY frontend/package*.json ./

# Install dependencies
RUN npm install --silent

# Copy source and build
COPY frontend/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Build Backend Dependencies
# -----------------------------------------------------------------------------
FROM ${BASE_PYTHON_IMAGE} AS backend-builder

WORKDIR /app

# Install build dependencies for WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 3: Production Image
# -----------------------------------------------------------------------------
FROM ${BASE_PYTHON_IMAGE} AS production

# Labels for container metadata
LABEL org.opencontainers.image.title="GPO Analysis Tool"
LABEL org.opencontainers.image.description="Cross-platform Active Directory GPO analyzer"
LABEL org.opencontainers.image.source="https://github.com/sevostianvitalii/GPOanalysis"

WORKDIR /app

# Install runtime dependencies for WeasyPrint PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libffi-dev \
    shared-mime-info \
    ca-certificates \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/uploads /app/exports

# Copy Python packages from builder
COPY --from=backend-builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy backend application
COPY backend/ ./backend/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist /app/static

# Copy nginx and supervisor configs
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/api/health || exit 1

# Start supervisor (manages nginx + uvicorn)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
