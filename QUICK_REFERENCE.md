# Impact Analyzer - Quick Reference Card

## 🚀 Getting Started (< 5 minutes)

```bash
# 1. Start all services
docker-compose up -d

# 2. Verify services are running
docker-compose ps

# 3. Test endpoints
curl http://localhost:8001/health  # ✅ Repository Scanner
curl http://localhost:8002/health  # ✅ AI Orchestrator  
curl http://localhost:8003/health  # ✅ Impact Analyzer
```

---

## 📡 Service Ports & Endpoints

| Service | Port | Health Check | Main Endpoint |
|---------|------|--------------|---------------|
| Repository Scanner | 8001 | `GET /health` | `POST /scan` |
| AI Orchestrator | 8002 | `GET /health` | `POST /api/v1/analyze` |
| Impact Analyzer | 8003 | `GET /health` | `POST /api/v1/analyze/impact` |
| MongoDB | 27017 | - | Direct connection |
| Redis | 6379 | - | Direct connection |
| PostgreSQL | 5432 | - | Direct connection |

---

## 🔧 Essential Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f repository-scanner

# Restart a service
docker-compose restart ai-orchestrator

# Execute commands in container
docker exec impact-repo-scanner ls -la

# Full cleanup (includes volumes)
docker-compose down -v
```

---

## 📊 Complete Analysis Workflow

```bash
# 1. Scan repository and build dependency graph
curl -X POST http://localhost:8001/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/org/repo.git",
    "branch": "main",
    "repo_id": "my-repo"
  }'

# 2. Run impact analysis
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "change_description": "Modified payment logic",
    "affected_files": ["src/payment.py", "src/api/checkout.py"],
    "repo_id": "my-repo",
    "branch": "main"
  }'

# 3. Get detailed impact metrics
curl -X POST http://localhost:8003/api/v1/analyze/impact \
  -H "Content-Type: application/json" \
  -d '{
    "changed_files": ["src/payment.py"],
    "graph_data": {"nodes": [...], "links": [...]}
  }'
```

---

## 🗄️ Database Access

```bash
# MongoDB
docker exec -it impact-mongodb mongosh -u admin -p admin

# Redis
docker exec -it impact-redis redis-cli

# PostgreSQL (optional)
docker exec -it impact-postgres psql -U postgres

# Check MongoDB collections
db.getCollections()
db.graphs.find().pretty()
```

---

## 📋 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables (secrets, API keys) |
| `docker-compose.yml` | Service definitions & dependencies |
| `services/*/Dockerfile` | Container build instructions |
| `services/*/requirements.txt` | Python dependencies |
| `config/prompts.yaml` | AI agent system prompts |

---

## ⚙️ Environment Variables (`.env`)

```env
# Essentials
OPENAI_API_KEY=sk-your-key-here
MONGO_USER=admin
MONGO_PASSWORD=admin

# Recommended for production
JWT_SECRET=your-32-character-minimum-secret
LOG_LEVEL=INFO

# Advanced (optional)
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
CRITICALITY_THRESHOLD=0.7
```

---

## 🧪 Test the API

```bash
# Health check
curl http://localhost:8001/health | jq

# List Swagger docs
curl http://localhost:8001/docs

# Minimal impact analysis
curl -X POST http://localhost:8003/api/v1/analyze/impact \
  -H "Content-Type: application/json" \
  -d '{
    "changed_files": ["test.py"],
    "graph_data": {"directed": true, "nodes": [{"id": "test"}], "links": []}
  }' | jq
```

---

## ❌ Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | Change port in `docker-compose.yml` or `lsof -i :PORT` |
| Out of memory | Increase Docker memory limit or add `mem_limit: 4g` |
| Services not starting | Run `docker-compose logs` to see errors |
| MongoDB connection failed | Wait 10s, check `docker-compose ps`, restart with `docker-compose restart` |
| API key errors | Verify `OPENAI_API_KEY` in `.env` and restart services |

---

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Startup time | ~30-60 seconds |
| Health check response | <100ms |
| Small analysis (<10 files) | 2-5 seconds |
| Large analysis (<100 files) | 10-30 seconds |
| Concurrent requests | 100+ per minute |
| Memory usage | ~2GB (adjustable) |

---

## 🔐 Security Best Practices

```bash
# 1. Change default credentials
MONGO_PASSWORD=your-secure-password
DB_PASSWORD=your-secure-password

# 2. Set strong JWT secret (min 32 chars)
JWT_SECRET=$(openssl rand -base64 32)

# 3. Use environment variables, never hardcode
# ✅ Good: OPENAI_API_KEY=${OPENAI_API_KEY}
# ❌ Bad: OPENAI_API_KEY=sk-xxxxx

# 4. Restrict database access
# Only expose ports to trusted networks
```

---

## 📈 Monitoring

```bash
# CPU & Memory usage
docker stats

# Container details
docker inspect impact-repo-scanner

# Network analysis
docker network ls
docker network inspect impact-network

# Log analysis
docker logs --since 1h impact-ai-orchestrator
```

---

## 🚀 Next Steps

1. **Read Full Documentation**
   - `DEPLOYMENT_GUIDE.md` - Complete setup instructions
   - `API_REFERENCE.md` - All API endpoints
   - `IMPLEMENTATION_SUMMARY.md` - Architecture details

2. **Set Up Production**
   - Configure `.env` with real credentials
   - Set up monitoring & logging
   - Run load tests
   - Set up backups

3. **Integrate with Your System**
   - Use the REST APIs
   - Build a frontend UI
   - Create CI/CD pipelines
   - Set up webhooks

---

## 📞 Quick Help

```bash
# Show this quick reference
cat QUICK_REFERENCE.md

# View deployment guide
cat DEPLOYMENT_GUIDE.md

# View API documentation
cat API_REFERENCE.md

# View implementation details
cat IMPLEMENTATION_SUMMARY.md

# View architecture
cat "Impact Unplugged Hackathon_ Comprehensive Architec.md"
```

---

*Last Updated: November 16, 2025*
*For detailed information, see DEPLOYMENT_GUIDE.md*
