# Deployment Checklist & Troubleshooting

## Pre-Deployment Validation

Run this before deploying to verify everything is set up correctly:

```bash
# Make scripts executable
chmod +x validate.sh diagnose.sh startup.sh

# Validate all files are in place
./validate.sh

# Diagnose system readiness
./diagnose.sh
```

---

## Quick Deployment

```bash
# Step 1: Verify setup
./validate.sh

# Step 2: Start services
docker-compose up -d

# Step 3: Wait for initialization (30-60 seconds)
sleep 30

# Step 4: Verify services are running
docker-compose ps

# Step 5: Test each service
curl http://localhost:8001/health  # Repository Scanner
curl http://localhost:8002/health  # AI Orchestrator
curl http://localhost:8003/health  # Impact Analyzer

# Expected output: {"status": "healthy", ...}
```

---

## Troubleshooting Guide

### Issue: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker service
sudo systemctl start docker

# Or on Mac:
# Open Docker Desktop application

# Verify Docker is running
docker ps
```

---

### Issue: "Port already in use"

**Solution:**
```bash
# Check what's using the port
lsof -i :8001    # For port 8001
lsof -i :8002    # For port 8002
lsof -i :8003    # For port 8003

# Either:
# 1. Kill the process using that port
#    lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9

# 2. Or change the port in docker-compose.yml
#    ports:
#      - "8011:8001"  # Use 8011 instead of 8001
```

---

### Issue: "Build failed: requirements not found"

**Solution:**
```bash
# Verify requirements files exist
ls -la services/repository-scanner/requirements.txt
ls -la services/impact-analyzer/requirements.txt
ls -la services/ai-orchestrator/requirements.txt

# Run validation
./validate.sh
```

---

### Issue: "MongoDB health check failed"

**Solution:**
```bash
# Wait longer for MongoDB to start
sleep 60

# Check MongoDB logs
docker logs impact-mongodb

# Restart MongoDB
docker-compose restart mongodb

# Verify with health check
docker-compose ps mongodb
```

---

### Issue: "Services in unhealthy state"

**Solution:**
```bash
# Check all logs
docker-compose logs

# Check specific service
docker-compose logs repository-scanner
docker-compose logs impact-analyzer
docker-compose logs ai-orchestrator

# Restart all services
docker-compose restart

# Or full restart
docker-compose down
docker-compose up -d
```

---

### Issue: "Out of memory errors"

**Solution:**
```bash
# Increase Docker memory limit
# In Docker Desktop: Settings > Resources > Memory (set to 4GB+)

# Or in docker-compose.yml add:
services:
  ai-orchestrator:
    mem_limit: 4g
    memswap_limit: 4g
```

---

### Issue: "Module not found errors in logs"

**Solution:**
```bash
# Rebuild containers without cache
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Or just rebuild specific service
docker-compose build --no-cache repository-scanner
docker-compose up -d repository-scanner
```

---

### Issue: "Services keep restarting"

**Solution:**
```bash
# Check full logs to see the error
docker-compose logs -f --tail=100

# Common causes:
# 1. MongoDB/Redis not healthy - wait and restart
# 2. Port conflict - change ports
# 3. Missing dependencies - rebuild

# Full reset:
docker-compose down -v
rm -rf config/chroma_db  # Remove persistent ChromaDB
docker-compose up -d
```

---

## Health Check Verification

After deployment, verify all services are healthy:

```bash
#!/bin/bash
echo "Checking Impact Analyzer Services..."
echo ""

services=(
  "repository-scanner:8001"
  "ai-orchestrator:8002"
  "impact-analyzer:8003"
)

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    response=$(curl -s http://localhost:$port/health 2>/dev/null || echo '{}')
    status=$(echo $response | grep -o '"status":"healthy"' || echo "")
    
    if [ ! -z "$status" ]; then
        echo "✅ $name (port $port) - HEALTHY"
    else
        echo "❌ $name (port $port) - FAILED"
        echo "   Response: $response"
    fi
done

echo ""
echo "Checking Databases..."

# MongoDB
if docker exec impact-mongodb mongosh -u admin -p admin --eval "db.adminCommand('ping')" 2>/dev/null | grep -q "ok"; then
    echo "✅ MongoDB - HEALTHY"
else
    echo "❌ MongoDB - NOT RESPONDING"
fi

# Redis
if docker exec impact-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo "✅ Redis - HEALTHY"
else
    echo "❌ Redis - NOT RESPONDING"
fi

echo ""
echo "Health check complete!"
```

Save this as `health-check.sh` and run:
```bash
chmod +x health-check.sh
./health-check.sh
```

---

## Complete Workflow Test

Once services are healthy, test the complete workflow:

```bash
#!/bin/bash

echo "Testing Complete Impact Analyzer Workflow"
echo ""

# 1. Test Repository Scanner
echo "1. Testing Repository Scanner /health endpoint..."
curl -s http://localhost:8001/health | jq . || echo "Failed"
echo ""

# 2. Test Impact Analyzer /health endpoint
echo "2. Testing Impact Analyzer /health endpoint..."
curl -s http://localhost:8003/health | jq . || echo "Failed"
echo ""

# 3. Test AI Orchestrator /health endpoint
echo "3. Testing AI Orchestrator /health endpoint..."
curl -s http://localhost:8002/health | jq . || echo "Failed"
echo ""

# 4. Test Impact Analyzer calculation
echo "4. Testing impact analysis endpoint..."
curl -s -X POST http://localhost:8003/api/v1/analyze/impact \
  -H "Content-Type: application/json" \
  -d '{
    "changed_files": ["test.py"],
    "graph_data": {
      "directed": true,
      "nodes": [{"id": "test.py"}],
      "links": []
    }
  }' | jq . || echo "Failed"
echo ""

echo "✅ Workflow test complete!"
```

Save as `workflow-test.sh`:
```bash
chmod +x workflow-test.sh
./workflow-test.sh
```

---

## Performance Baseline

After successful deployment, check performance:

```bash
# Container resource usage
docker stats --no-stream

# Expected baseline (per container):
# Repository Scanner: ~200-300MB RAM
# Impact Analyzer: ~150-250MB RAM
# AI Orchestrator: ~300-500MB RAM
# MongoDB: ~200-400MB RAM
# Redis: ~50-100MB RAM
```

---

## Logs & Debugging

```bash
# View all logs
docker-compose logs

# View logs for specific service
docker-compose logs repository-scanner
docker-compose logs impact-analyzer
docker-compose logs ai-orchestrator

# Follow logs in real-time
docker-compose logs -f

# Follow specific service logs
docker-compose logs -f repository-scanner

# Get last N lines
docker-compose logs --tail=50

# Filter by timestamp
docker-compose logs --since 2025-11-16T10:00:00
```

---

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Full shutdown
docker-compose down

# Full cleanup (removes volumes)
docker-compose down -v

# View running containers
docker-compose ps

# Execute command in container
docker exec -it impact-repo-scanner bash

# Check container environment
docker inspect impact-repo-scanner

# View resource usage
docker stats
```

---

## Success Indicators

✅ All checks passing when you see:

```
✅ .env exists
✅ docker-compose.yml exists
✅ services/repository-scanner/Dockerfile exists
✅ services/impact-analyzer/Dockerfile exists
✅ services/ai-orchestrator/Dockerfile exists
✅ services/repository-scanner/src/main.py exists
✅ services/impact-analyzer/src/main.py exists
✅ services/ai-orchestrator/src/main.py exists
... (all files)
✅ Docker & Docker Compose available
✅ Docker daemon is running
✅ docker-compose.yml syntax is valid
✅ All services are healthy (from curl tests)
✅ All databases responding
```

---

## Next Steps After Deployment

1. ✅ Verify all services are running
2. ✅ Test health endpoints
3. ✅ Test complete workflow
4. ✅ Configure OpenAI API key for full features
5. ✅ Set up monitoring
6. ✅ Integrate with your application

---

For more help, see:
- `DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `QUICK_REFERENCE.md` - Quick commands
- `API_REFERENCE.md` - API documentation
