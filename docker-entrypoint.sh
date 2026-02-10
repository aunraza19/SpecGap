#!/bin/sh
set -e

echo "🚀 Starting SpecGap Application..."

# Start uvicorn in the background
echo "📡 Starting Backend API on port 8000..."
cd /app/specgap
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info

