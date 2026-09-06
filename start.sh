#!/bin/sh
# ==========================================================
# All-in-One Startup Script for Unified Container
# Runs FastAPI (Service B) + Express & React Frontend (Service A)
# ==========================================================

set -e

echo "🚀 Starting Python FastAPI Intelligence Engine (Service B) on 127.0.0.1:8000..."
uvicorn app.server:app --host 127.0.0.1 --port 8000 &
FASTAPI_PID=$!

# Wait briefly for FastAPI to bind to port 8000
echo "⏳ Waiting for FastAPI internal engine to be ready..."
for i in $(seq 1 30); do
  if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    echo "✅ FastAPI is ready (PID: $FASTAPI_PID)!"
    break
  fi
  sleep 1
done

echo "🚀 Starting Node.js Express Gateway & React SPA on port ${PORT:-5000}..."
cd /app/backend-express
export FASTAPI_BASE_URL="http://127.0.0.1:8000"
exec node server.js
