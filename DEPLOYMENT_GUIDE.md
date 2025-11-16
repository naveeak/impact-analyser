# Deployment Guide - Impact Analyzer

## Quick Start

### Prerequisites
- Docker & Docker Compose installed (v20.10+)
- 4GB RAM minimum
- 5GB disk space

### 1. Start Services

```bash
# Clone or navigate to the project
cd /workspaces/impact-analyser

# Option A: Using the startup script (recommended)
chmod +x startup.sh
./startup.sh

# Option B: Manual startup
docker-compose up -d
```

### 2. Verify Services Are Running

```bash
# Check all containers
docker-compose ps

# Test health endpoints
curl http://localhost:8001/health  # Repository Scanner
curl http://localhost:8002/health  # AI Orchestrator  
curl http://localhost:8003/health  # Impact Analyzer
```

### 3. Configure Environment (Production)

Edit `.env` with your settings:

```bash
# Most important for production
OPENAI_API_KEY=sk-your-actual-key-here

# Other production settings
MONGO_USER=your-mongo-user
MONGO_PASSWORD=your-secure-password
DB_PASSWORD=your-secure-postgres-password
JWT_SECRET=your-very-secure-jwt-secret-min-32-chars
```

---

## System Architecture

```
┌─────────────────────────────────────────────┐
│         Client Applications                 │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │  Load Balancer      │
        │  (Optional)         │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        │  API Gateway        │
        │  (Optional)         │
        └──┬─────────────┬────┘
           │             │
    ┌──────▼──┐   ┌─────▼────┐
    │Repository│   │  Impact  │
    │ Scanner  │   │Analyzer  │
    │:8001     │   │:8003     │
    └──────┬───┘   └────┬─────┘
           │            │
    ┌──────▼───────────▼────┐
    │  AI Orchestrator      │
    │  (LangGraph + RAG)    │
    │  :8002                │
    └──────────┬────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼──┐  ┌───▼───┐  ┌──▼────┐
│Mongo │  │Redis  │  │Chrome │
│:27017│  │:6379  │  │DB     │
└──────┘  └───────┘  └───────┘
```

---

## Service Details

### Repository Scanner (Port 8001)
**Purpose:** Clone repositories and build dependency graphs
**Functions:**
- Clone Git repositories
- Parse Python/JavaScript/Java code
- Extract dependencies and relationships
- Store graphs in MongoDB
- Cache results in Redis

**Configuration:**
```env
GIT_CLONE_PATH=/app/repos
LOG_LEVEL=INFO
```

### Impact Analyzer (Port 8003)
**Purpose:** Analyze impact of code changes
**Functions:**
- Graph traversal algorithms (BFS/DFS)
- Criticality scoring
- Risk classification
- Dependency path analysis

**Configuration:**
```env
CRITICALITY_THRESHOLD=0.7
LOG_LEVEL=INFO
```

### AI Orchestrator (Port 8002)
**Purpose:** LangGraph workflow with 6 specialized agents
**Functions:**
- Query planning and parsing
- Dependency analysis
- RAG (Retrieval-Augmented Generation)
- Impact scoring
- Test planning
- Report generation

**Configuration:**
```env
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=10
```

---

## Data Persistence

### MongoDB (Port 27017)
- Stores dependency graphs (node-link JSON format)
- Stores analysis reports
- Stores vector embeddings metadata
- **Default credentials:** admin / admin

### Redis (Port 6379)
- Caches dependency graphs (TTL: 24 hours)
- Caches analysis results
- Session storage

### PostgreSQL (Port 5432) - Optional
- User accounts (when using API Gateway)
- Audit logs
- **Default credentials:** postgres / postgres

---

## Common Operations

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f repository-scanner
docker-compose logs -f ai-orchestrator
docker-compose logs -f impact-analyzer
```

### Stop Services

```bash
# Graceful shutdown
docker-compose down

# Full cleanup (including volumes)
docker-compose down -v
```

### Restart Services

```bash
# Restart specific service
docker-compose restart repository-scanner

# Restart all services
docker-compose restart
```

### Access Databases

```bash
# MongoDB shell
docker exec -it impact-mongodb mongosh -u admin -p admin

# Redis CLI
docker exec -it impact-redis redis-cli

# PostgreSQL
docker exec -it impact-postgres psql -U postgres -d impact_analysis
```

---

## API Usage Examples

### 1. Scan a Repository

```bash
curl -X POST http://localhost:8001/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/org/repo.git",
    "branch": "main",
    "repo_id": "my-repo"
  }'
```

### 2. Analyze Impact

```bash
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "change_description": "Modified payment processing",
    "affected_files": ["src/payment.py"],
    "repo_id": "my-repo",
    "branch": "main"
  }'
```

### 3. Calculate Criticality

```bash
curl -X POST http://localhost:8003/api/v1/criticality/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "directed": true,
    "nodes": [...],
    "links": [...]
  }'
```

---

## Troubleshooting

### Issue: Services fail to start

**Solution:**
```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Out of memory

**Solution:**
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or in docker-compose.yml, add:
services:
  ai-orchestrator:
    mem_limit: 4g
    memswap_limit: 4g
```

### Issue: Port already in use

**Solution:**
```bash
# Find process using port
lsof -i :8001

# Or change port in docker-compose.yml
ports:
  - "8001:8001"  # Change first number to different port
```

### Issue: MongoDB connection failed

**Solution:**
```bash
# Check MongoDB is running
docker-compose ps mongodb

# Restart MongoDB
docker-compose restart mongodb

# Wait a few seconds, then retry
sleep 5
curl http://localhost:8001/health
```

### Issue: API key errors

**Solution:**
```bash
# Set valid OpenAI API key
export OPENAI_API_KEY=sk-your-actual-key

# Or update .env file
OPENAI_API_KEY=sk-your-actual-key

# Restart AI Orchestrator
docker-compose restart ai-orchestrator
```

---

## Performance Tuning

### For Better Performance

1. **Increase MongoDB cache:**
```bash
docker-compose down
# Edit docker-compose.yml, add to mongodb:
#   command: mongod --cache-size-gb 2
docker-compose up -d
```

2. **Use more Redis memory:**
```bash
# Edit docker-compose.yml, modify redis command:
#   command: redis-server --appendonly yes --maxmemory 2gb
```

3. **Enable parallel processing:**
```env
ENABLE_PARALLEL_ANALYSIS=true
```

4. **Adjust RAG chunk size:**
```env
CHUNK_SIZE=2000        # Larger = fewer requests, slower
CHUNK_OVERLAP=400      # Larger = more context, more tokens
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Update `.env` with production values
- [ ] Set valid `OPENAI_API_KEY`
- [ ] Change database passwords
- [ ] Set strong `JWT_SECRET`
- [ ] Configure backup strategy
- [ ] Set up monitoring (optional)
- [ ] Configure log aggregation (optional)
- [ ] Test all endpoints
- [ ] Load testing completed

### Recommended Setup

1. **Use managed databases:**
   - MongoDB Atlas for production data
   - Redis Cloud for caching
   - RDS for PostgreSQL (if using API Gateway)

2. **Add monitoring:**
```bash
# Create prometheus.yml and grafana setup
# Or use cloud monitoring services
```

3. **Add logging:**
```bash
# Send logs to CloudWatch, Stackdriver, or ELK stack
```

4. **Security hardening:**
- Use SSL/TLS certificates
- Configure firewall rules
- Enable authentication
- Regular security audits

---

## Scaling

### Horizontal Scaling

For production with heavy load:

```yaml
# docker-compose-prod.yml
version: '3.8'
services:
  repository-scanner:
    deploy:
      replicas: 3
  impact-analyzer:
    deploy:
      replicas: 2
  ai-orchestrator:
    deploy:
      replicas: 2
```

### Vertical Scaling

Increase resource limits:

```yaml
services:
  ai-orchestrator:
    mem_limit: 8g
    cpus: 4
```

---

## Backup & Recovery

### Backup MongoDB

```bash
docker exec impact-mongodb mongodump \
  --uri "mongodb://admin:admin@localhost:27017/" \
  --out /backup/mongo
```

### Restore MongoDB

```bash
docker exec -it impact-mongodb mongorestore \
  --uri "mongodb://admin:admin@localhost:27017/" \
  /backup/mongo
```

---

## Health Monitoring

Create a monitoring script:

```bash
#!/bin/bash
while true; do
  echo "$(date): Checking services..."
  curl -s http://localhost:8001/health | jq .status
  curl -s http://localhost:8002/health | jq .status
  curl -s http://localhost:8003/health | jq .status
  sleep 60
done
```

---

## Support & Documentation

- **API Reference:** See `API_REFERENCE.md`
- **Implementation Details:** See `IMPLEMENTATION_SUMMARY.md`
- **Architecture:** See `Impact Unplugged Hackathon_ Comprehensive Architec.md`

---

*Last Updated: November 16, 2025*
