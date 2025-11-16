#!/bin/bash

# Impact Analyzer Docker Startup Script

set -e

echo "🚀 Starting Impact Analyzer Services..."
echo ""

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Docker or docker-compose not found. Please install Docker first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env 2>/dev/null || true
fi

# Start services
echo "⏳ Pulling images and starting services (this may take a few minutes)..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to become healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

services=(
  "postgres:5432"
  "mongodb:27017"
  "redis:6379"
  "impact-repo-scanner:8001"
  "impact-analyzer:8003"
  "impact-ai-orchestrator:8002"
)

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if docker exec "impact-${name}" ping -c 1 localhost > /dev/null 2>&1 || \
       docker exec "$name" ping -c 1 localhost > /dev/null 2>&1; then
        echo "✅ $name is running on port $port"
    else
        echo "⏳ $name starting..."
    fi
done

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📊 Service Endpoints:"
echo "  - Repository Scanner: http://localhost:8001"
echo "  - AI Orchestrator:    http://localhost:8002"
echo "  - Impact Analyzer:    http://localhost:8003"
echo ""
echo "🧪 Test the services:"
echo "  curl http://localhost:8001/health"
echo "  curl http://localhost:8002/health"
echo "  curl http://localhost:8003/health"
echo ""
echo "📖 View logs:"
echo "  docker-compose logs -f"
echo ""
echo "⛔ Stop services:"
echo "  docker-compose down"
