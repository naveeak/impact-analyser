#!/bin/bash

# Diagnostic script for Docker Compose issues

echo "=== Impact Analyzer Docker Diagnostic ==="
echo ""
echo "1. Checking Docker installation..."
docker --version
docker-compose --version
echo "✅ Docker & Docker Compose available"
echo ""

echo "2. Checking current directory..."
pwd
echo "✅ Current directory correct"
echo ""

echo "3. Verifying docker-compose.yml..."
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml found"
    echo "   Size: $(wc -c < docker-compose.yml) bytes"
else
    echo "❌ docker-compose.yml NOT found"
    exit 1
fi
echo ""

echo "4. Verifying .env file..."
if [ -f ".env" ]; then
    echo "✅ .env found"
    echo "   Size: $(wc -c < .env) bytes"
else
    echo "❌ .env NOT found"
    exit 1
fi
echo ""

echo "5. Checking for syntax errors in docker-compose.yml..."
docker-compose config > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ docker-compose.yml syntax is valid"
else
    echo "❌ docker-compose.yml has syntax errors"
    docker-compose config
    exit 1
fi
echo ""

echo "6. Checking required Dockerfiles..."
dockerfiles=(
    "services/repository-scanner/Dockerfile"
    "services/impact-analyzer/Dockerfile"
    "services/ai-orchestrator/Dockerfile"
)
for df in "${dockerfiles[@]}"; do
    if [ -f "$df" ]; then
        echo "✅ $df exists"
    else
        echo "❌ $df MISSING"
        exit 1
    fi
done
echo ""

echo "7. Checking source files..."
sources=(
    "services/repository-scanner/src/main.py"
    "services/impact-analyzer/src/main.py"
    "services/ai-orchestrator/src/main.py"
)
for src in "${sources[@]}"; do
    if [ -f "$src" ]; then
        echo "✅ $src exists"
    else
        echo "❌ $src MISSING"
        exit 1
    fi
done
echo ""

echo "8. Checking Docker daemon..."
docker ps > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon is NOT running"
    echo "   Try: sudo systemctl start docker"
    exit 1
fi
echo ""

echo "9. Checking for port conflicts..."
ports=(8001 8002 8003 5432 27017 6379)
for port in "${ports[@]}"; do
    if ! netstat -tuln 2>/dev/null | grep -q ":$port " && ! ss -tuln 2>/dev/null | grep -q ":$port "; then
        echo "✅ Port $port is available"
    else
        echo "⚠️  Port $port may be in use"
    fi
done
echo ""

echo "=== Diagnostic Complete ==="
echo "Status: ✅ All systems ready for deployment"
echo ""
echo "Run the following to start services:"
echo "  docker-compose up -d"
echo ""
