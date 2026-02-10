# ============================================
# SpecGap - Multi-stage Docker Build
# Backend: FastAPI + Python
# Frontend: React + Vite (served via nginx)
# ============================================

# ============== STAGE 1: Frontend Build ==============
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files first for better caching
COPY Frontend/package.json Frontend/package-lock.json* Frontend/bun.lockb* ./

# Install dependencies
RUN npm ci --legacy-peer-deps || npm install --legacy-peer-deps

# Copy frontend source
COPY Frontend/ ./

# Build for production with API URL
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}

RUN npm run build


# ============== STAGE 2: Python Backend ==============
FROM python:3.11-slim AS backend

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/specgap \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    poppler-utils \
    tesseract-ocr \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY specgap/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY specgap/ ./specgap/

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist /app/static

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy startup script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /var/log/nginx && \
    chown -R appuser:appuser /var/lib/nginx && \
    chown -R appuser:appuser /run

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose ports
EXPOSE 8000

# Set workdir to specgap for running the app
WORKDIR /app/specgap

# Run as non-root user
USER appuser

# Start both nginx and uvicorn
ENTRYPOINT ["/app/docker-entrypoint.sh"]

