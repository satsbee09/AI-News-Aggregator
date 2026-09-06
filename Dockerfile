# ==========================================================
# All-in-One Unified Dockerfile for AI News Aggregator
# Bundles: React 19 Frontend + Node.js Express Gateway + Python FastAPI Engine
# Designed for 1-Click Single Service Deployment on Render / Railway / Docker
# ==========================================================

FROM python:3.12-slim

# Prevent Python buffer delays & pyc clutter
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_ENV=production \
    PORT=5000

WORKDIR /app

# 1. Install system utilities and Node.js 20
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies using uv for maximum build speed
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# 3. Build React 19 Frontend static assets
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --include=dev --silent
COPY frontend/ ./
RUN npm run build && rm -rf node_modules

# 4. Install Node.js Express dependencies
WORKDIR /app/backend-express
COPY backend-express/package*.json ./
RUN npm ci --omit=dev --silent
COPY backend-express/ ./

# 5. Copy FastAPI Python application files & Startup Script
WORKDIR /app
COPY app/ ./app/
COPY main.py .
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 5000

# Healthcheck targeting Express health route (which checks MongoDB & FastAPI)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/api/health || exit 1

CMD ["/app/start.sh"]
