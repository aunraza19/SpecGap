# ============================================
# SpecGap - Multi-stage Docker Build
# Backend: FastAPI + Python
# Frontend: React + Vite (served by FastAPI)
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

# Build for production
# Note: In production, API calls go to same origin /api/v1
ENV VITE_API_URL=/api

RUN npm run build

# Verify build output
RUN ls -la dist/ && ls -la dist/assets/ || true


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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY specgap/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY specgap/ ./specgap/

# Copy built frontend from stage 1 to /app/static
COPY --from=frontend-builder /app/frontend/dist /app/static

# Verify static files exist
RUN echo "=== Static files ===" && ls -la /app/static/ && ls -la /app/static/assets/ || echo "No assets folder"

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set workdir to specgap for running the app
WORKDIR /app/specgap

# Run as non-root user
USER appuser

# Start uvicorn directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

