# API Reference Guide

## 📋 Base URLs

- **API Gateway**: `http://localhost:3000/api/v1`
- **Repository Scanner**: `http://localhost:8001`
- **Impact Analyzer**: `http://localhost:8003`
- **AI Orchestrator**: `http://localhost:8002`

## 🏥 Health Checks

All services provide health check endpoints:

```http
GET /health

Response:
{
  "status": "healthy",
  "service": "service-name",
  "timestamp": "2024-01-15T10:30:00Z",
  "dependencies": {
    "mongodb": "healthy",
    "redis": "healthy"
  }
}
```

---

## 📦 Repository Scanner Service (Port 8001)

### 1. Scan Repository
```http
POST /scan
Content-Type: application/json

{
  "repo_url": "https://github.com/org/repo.git",
  "branch": "main",
  "repo_id": "unique-repo-id"
}

Response:
{
  "scan_id": "scan_unique-repo-id_1705318200.0",
  "repo_id": "unique-repo-id",
  "status": "processing",
  "message": "Scan started in background",
  "graph_id": null
}
```

### 2. Get Scan Status
```http
GET /scan/{scan_id}

Response:
{
  "scan_id": "scan_...",
  "repo_id": "unique-repo-id",
  "status": "completed",
  "message": "Scan completed successfully",
  "graph_id": "graph-uuid"
}
```

### 3. Get Dependency Graph
```http
GET /graph/{repo_id}?branch=main

Response:
{
  "graph_id": "graph-uuid",
  "repo_id": "unique-repo-id",
  "nodes_count": 150,
  "edges_count": 280,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 4. Get Changed Files
```http
GET /changed-files/{repo_id}?commit_sha=abc123...

Response:
{
  "repo_id": "unique-repo-id",
  "commit_sha": "abc123...",
  "changed_files": [
    "src/payment/processor.py",
    "src/api/checkout.py"
  ],
  "count": 2
}
```

---

## 📊 Impact Analyzer Service (Port 8003)

### 1. Analyze Impact
```http
POST /api/v1/analyze/impact
Content-Type: application/json

{
  "changed_files": ["src/payment/processor.py", "src/api/checkout.py"],
  "graph_data": {
    "directed": true,
    "multigraph": false,
    "graph": {},
    "nodes": [...],
    "links": [...]
  }
}

Response:
{
  "changed_files": [...],
  "impacted_components": ["service_x", "api_y", "cache_z"],
  "impacted_count": 3,
  "criticality_scores": {
    "service_x": 0.85,
    "api_y": 0.72,
    "cache_z": 0.45
  },
  "high_risk_areas": ["service_x", "api_y"],
  "risk_level": "HIGH",
  "affected_services": ["payment", "checkout"],
  "recommendations": [
    "High impact detected. Plan comprehensive testing",
    "Deploy with caution, monitor all affected endpoints"
  ]
}
```

### 2. Calculate Criticality Scores
```http
POST /api/v1/criticality/calculate
Content-Type: application/json

{
  "directed": true,
  "nodes": [...],
  "links": [...]
}

Response:
{
  "status": "success",
  "node_count": 150,
  "criticality_scores": {
    "node_id_1": 0.92,
    "node_id_2": 0.65,
    ...
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 3. Analyze Path Between Nodes
```http
POST /api/v1/path/analyze?source=file_a&target=api_y
Content-Type: application/json

{
  "directed": true,
  "nodes": [...],
  "links": [...]
}

Response:
{
  "source": "file_a",
  "target": "api_y",
  "path_count": 3,
  "paths": [
    ["file_a", "module_b", "service_x", "api_y"],
    ["file_a", "service_x", "api_y"],
    ...
  ],
  "shortest_path": ["file_a", "service_x", "api_y"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. Get Graph Statistics
```http
POST /api/v1/graph/stats
Content-Type: application/json

{
  "directed": true,
  "nodes": [...],
  "links": [...]
}

Response:
{
  "status": "success",
  "stats": {
    "node_count": 150,
    "edge_count": 280,
    "density": 0.012,
    "is_dag": true,
    "is_connected": true,
    "number_of_components": 1,
    "average_degree": 3.7,
    "top_central_nodes": [
      {"node": "core_module", "centrality": 0.45},
      ...
    ]
  }
}
```

---

## 🤖 AI Orchestrator Service (Port 8002)

### 1. Run Impact Analysis (Synchronous)
```http
POST /api/v1/analyze
Content-Type: application/json

{
  "change_description": "Modified payment processing logic in checkout module",
  "affected_files": [
    "src/payment/processor.py",
    "src/api/checkout.py"
  ],
  "repo_id": "test_repo_123",
  "branch": "main",
  "dependency_graph": null
}

Response:
{
  "analysis_id": "analysis_...",
  "status": "completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "repo_id": "test_repo_123",
  "branch": "main",
  "change_description": "...",
  "impact_analysis": {
    "affected_components": ["payment_module", "checkout_service"],
    "analysis_type": "dependency_graph",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "criticality_scores": {
    "criticality": 0.75,
    "risk": 0.82,
    "testing_scope": 0.6
  },
  "test_plan": {
    "priority_1_critical": {
      "description": "Core payment flow",
      "tests": ["test_payment_success", "test_payment_failure"],
      "estimated_time": "5 minutes"
    },
    ...
  },
  "final_report": {
    "executive_summary": "This change affects the payment processing module with HIGH risk...",
    ...
  },
  "error": null
}
```

### 2. Run Analysis (Asynchronous)
```http
POST /api/v1/analyze/async
Content-Type: application/json

{
  "change_description": "...",
  "affected_files": [...],
  "repo_id": "test_repo_123",
  "branch": "main"
}

Response:
{
  "analysis_id": "async_analysis_...",
  "status": "processing",
  "message": "Analysis started in background",
  "timestamp": "2024-01-15T10:30:00Z"
}

# Then poll the result:
GET /api/v1/analyze/{analysis_id}
```

### 3. Index Documents (RAG)
```http
POST /api/v1/documents/index
Content-Type: application/json

{
  "documents": [
    "content of file 1...",
    "content of file 2...",
    ...
  ],
  "metadata": [
    {"file": "src/payment/processor.py", "language": "python"},
    {"file": "src/api/checkout.py", "language": "python"}
  ],
  "repo_id": "test_repo_123"
}

Response:
{
  "status": "success",
  "indexed_count": 45,
  "repo_id": "test_repo_123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 4. Retrieve Context (RAG)
```http
POST /api/v1/context/retrieve
Content-Type: application/json

{
  "query": "payment processing checkout flow",
  "k": 10
}

Response:
{
  "query": "payment processing checkout flow",
  "results": [
    {
      "content": "relevant code snippet...",
      "metadata": {"file": "src/payment/processor.py"},
      "relevance_score": 0.92
    },
    ...
  ],
  "count": 3
}
```

### 5. Get Document Statistics
```http
GET /api/v1/documents/stats

Response:
{
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z",
  "stats": {
    "collection_name": "code_analysis",
    "document_count": 150,
    "metadata_schema": {...}
  }
}
```

### 6. Clear Collection (Testing)
```http
POST /api/v1/documents/clear

Response:
{
  "status": "success",
  "message": "Vector store cleared",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🔐 Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

---

## 📝 Common Workflows

### Complete Analysis Workflow
```bash
# 1. Scan repository
curl -X POST http://localhost:8001/scan \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/org/repo.git",
    "branch": "main",
    "repo_id": "my-repo"
  }'

# 2. Wait for scan completion (poll the scan_id)
curl http://localhost:8001/scan/{scan_id}

# 3. Get dependency graph
curl http://localhost:8001/graph/my-repo

# 4. Run impact analysis
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "change_description": "Modified payment logic",
    "affected_files": ["src/payment.py"],
    "repo_id": "my-repo",
    "branch": "main"
  }'

# 5. Get results
# Response includes impact_analysis, criticality_scores, test_plan, final_report
```

### Testing Rate Limiting
```bash
# Single request
curl http://localhost:8002/health

# Multiple concurrent requests
for i in {1..101}; do
  curl http://localhost:8002/health &
done

# Should get 429 after 100 requests per minute
```

---

## 🧪 Test the API with curl

```bash
# Repository Scanner Health
curl -X GET http://localhost:8001/health | jq

# Impact Analyzer Health
curl -X GET http://localhost:8003/health | jq

# AI Orchestrator Health
curl -X GET http://localhost:8002/health | jq

# Full analysis workflow
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "change_description": "Test change",
    "affected_files": ["test.py"],
    "repo_id": "test",
    "branch": "main"
  }' | jq
```

---

## 📚 API Documentation

Swagger UI documentation available at:
- Repository Scanner: `http://localhost:8001/docs`
- Impact Analyzer: `http://localhost:8003/docs`
- AI Orchestrator: `http://localhost:8002/docs`

---

*Last Updated: November 16, 2025*
