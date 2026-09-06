#!/usr/bin/env bash
# ==========================================================
# Automated Deployment Script for AWS EC2 / Linux VPS
# AI News Aggregator & Intelligence Feed
# ==========================================================

set -e

echo "=========================================================="
echo "🚀 Starting AI News Aggregator Deployment on AWS EC2"
echo "=========================================================="

# 1. Update system packages
echo "📦 Updating OS package lists..."
if command -v apt-get &>/dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y curl git ca-certificates gnupg lsb-release
elif command -v dnf &>/dev/null; then
    sudo dnf update -y
    sudo dnf install -y curl git ca-certificates
fi

# 2. Install Docker & Docker Compose if not already installed
if ! command -v docker &>/dev/null; then
    echo "🐳 Docker not found. Installing Docker Engine..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm -f get-docker.sh
    echo "✅ Docker installed successfully."
else
    echo "✅ Docker is already installed: $(docker --version)"
fi

# Ensure Docker Compose plugin is present
if ! docker compose version &>/dev/null; then
    echo "📦 Installing Docker Compose plugin..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y docker-compose-plugin
    fi
fi

# Start & enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# 3. Verify .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found."
    if [ -f .env.production.example ]; then
        echo "📝 Creating .env from .env.production.example template..."
        cp .env.production.example .env
        echo "⚠️  PLEASE EDIT .env with your actual MongoDB URI, GROQ_API_KEY, and EMAIL credentials before running live traffic!"
    else
        echo "❌ Error: Neither .env nor .env.production.example exists."
        exit 1
    fi
fi

# 4. Pull updates and build Docker containers
echo "🔨 Building and launching all services via Docker Compose..."
sudo docker compose down --remove-orphans || true
sudo docker compose build --pull
sudo docker compose up -d

# 5. Check health & status
echo ""
echo "⏳ Waiting 10 seconds for services to initialize..."
sleep 10

echo ""
echo "=========================================================="
echo "📊 Deployment Status & Health Checks"
echo "=========================================================="
sudo docker compose ps

echo ""
echo "=========================================================="
echo "🎉 Deployment Complete!"
echo "=========================================================="
PUBLIC_IP=$(curl -s https://checkip.amazonaws.com || curl -s ifconfig.me || echo "<YOUR_EC2_PUBLIC_IP>")
echo "🌐 Your AI News Aggregator is now live at:"
echo "   http://${PUBLIC_IP}"
echo ""
echo "Useful Commands:"
echo " - View all logs:          sudo docker compose logs -f"
echo " - View FastAPI logs:      sudo docker compose logs -f fastapi-backend"
echo " - View Express logs:      sudo docker compose logs -f express-gateway"
echo " - Restart all services:   sudo docker compose restart"
echo " - Stop all services:      sudo docker compose down"
echo "=========================================================="
