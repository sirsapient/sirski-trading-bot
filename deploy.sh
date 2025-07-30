#!/bin/bash

# Sirski Trading Bot Deployment Script
# Usage: ./deploy.sh [local|vps|docker]

set -e

echo "🚀 Sirski Trading Bot Deployment"
echo "================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy env.example to .env and configure your settings:"
    echo "cp env.example .env"
    echo "nano .env"
    exit 1
fi

# Load environment variables
source .env

# Function to deploy locally
deploy_local() {
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    echo "🧪 Testing APIs..."
    python test_apis.py
    
    echo "🚀 Starting trading bot in paper mode..."
    python src/main.py --mode=paper
}

# Function to deploy with Docker
deploy_docker() {
    echo "🐳 Building Docker image..."
    docker build -t sirski-trading-bot .
    
    echo "🚀 Starting with Docker Compose..."
    docker-compose up -d
    
    echo "📊 Monitoring logs..."
    docker-compose logs -f trading-bot
}

# Function to deploy on VPS
deploy_vps() {
    echo "☁️  VPS Deployment Instructions:"
    echo ""
    echo "1. SSH into your VPS:"
    echo "   ssh user@your-vps-ip"
    echo ""
    echo "2. Install Docker:"
    echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "   sudo sh get-docker.sh"
    echo "   sudo usermod -aG docker $USER"
    echo ""
    echo "3. Clone your repository:"
    echo "   git clone <your-repo-url>"
    echo "   cd trading-bot"
    echo ""
    echo "4. Set up environment:"
    echo "   cp env.example .env"
    echo "   nano .env  # Add your wallet keys"
    echo ""
    echo "5. Deploy:"
    echo "   ./deploy.sh docker"
    echo ""
    echo "6. Monitor:"
    echo "   docker-compose logs -f"
}

# Main deployment logic
case "${1:-local}" in
    "local")
        deploy_local
        ;;
    "docker")
        deploy_docker
        ;;
    "vps")
        deploy_vps
        ;;
    *)
        echo "Usage: $0 [local|docker|vps]"
        echo ""
        echo "Options:"
        echo "  local   - Run locally with Python"
        echo "  docker  - Run with Docker Compose"
        echo "  vps     - Show VPS deployment instructions"
        exit 1
        ;;
esac 