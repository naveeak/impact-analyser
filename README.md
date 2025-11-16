# 🎯 AI-Powered Code Impact Analysis System

An intelligent, automated solution that transforms how developers understand code change impacts using RAG (Retrieval Augmented Generation), agentic workflows with LangGraph, and dependency graph analysis.

## 🚀 Overview

This tool automates the detection of code change impacts across complex applications, eliminating manual, time-consuming impact analysis processes.

### Key Features

- **Automated Impact Analysis**: AI-driven detection of affected components
- **Dependency Mapping**: Visual representation of direct and transitive dependencies
- **Risk Assessment**: Criticality scoring and risk classification (HIGH/MEDIUM/LOW)
- **Smart Test Planning**: Optimized, prioritized test coverage recommendations
- **Interactive Visualization**: Real-time dependency graphs and impact reports

## 🏗️ Architecture

### Microservices Architecture

```
┌─────────────────┐
│  API Gateway    │ ← OAuth2/JWT Authentication
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────────┬────────────┐
    ▼         ▼            ▼              ▼            ▼
┌────────┐ ┌──────┐  ┌──────────┐  ┌──────────┐  ┌──────┐
│Repo    │ │Impact│  │AI Orch.  │  │Test Gen. │  │Front │
│Scanner │ │Analyz│  │(LangGrph)│  │          │  │ end  │
└────────┘ └──────┘  └──────────┘  └──────────┘  └──────┘
```

### Technology Stack

- **Backend**: Python 3.11+ (FastAPI), Node.js 20+ (Express)
- **AI/ML**: LangChain, LangGraph, OpenAI GPT-4, ChromaDB
- **Databases**: PostgreSQL 16, MongoDB 7, Redis 7
- **Infrastructure**: Docker, Docker Compose
- **Frontend**: React 18+ with TypeScript, D3.js/Cytoscape.js

## 📦 Project Structure

```
impact-analysis-tool/
├── services/
│   ├── api-gateway/           # Authentication & routing
│   ├── repository-scanner/    # Code parsing & graph building
│   ├── impact-analyzer/       # Impact calculation
│   ├── ai-orchestrator/       # RAG & LangGraph workflows
│   ├── test-generator/        # Test plan generation
│   └── frontend/              # React UI
├── config/                    # Configuration files
├── docs/                      # Documentation
├── tests/                     # Integration & E2E tests
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Container orchestration
├── .env.example               # Environment template
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key
- Git

### Setup

1. **Clone and configure**:
```bash
git clone <repository-url>
cd impact-analysis-tool
cp .env.example .env
# Edit .env with your API keys
```

2. **Build containers**:
```bash
docker-compose build
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Verify health**:
```bash
curl http://localhost:3000/health
```

5. **Access the application**:
- Frontend: http://localhost:3000
- API Gateway: http://localhost:3000/api/v1
- API Documentation: http://localhost:3000/docs

## 🔧 Development

### Running Tests

```bash
# Unit tests for repository scanner
docker-compose exec repository-scanner pytest

# Unit tests for AI orchestrator
docker-compose exec ai-orchestrator pytest

# Integration tests
docker-compose exec api-gateway pytest tests/integration/

# E2E tests
npm run test:e2e
```

### Local Development

Each service can be run independently for development:

```bash
# Repository Scanner
cd services/repository-scanner
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8001

# AI Orchestrator
cd services/ai-orchestrator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8002
```

## 📚 API Documentation

### Core Endpoints

#### Repository Management
```http
POST /api/v1/repositories
Content-Type: application/json

{
  "repo_url": "https://github.com/org/repo",
  "branch": "main",
  "name": "My Application"
}
```

#### Scan Repository
```http
POST /api/v1/repositories/{id}/scan
```

#### Impact Analysis
```http
POST /api/v1/impact-analysis
Content-Type: application/json

{
  "repo_id": "abc123",
  "change_description": "Modified payment processing logic",
  "affected_files": ["src/payment/processor.py", "src/api/checkout.py"]
}
```

#### Get Analysis Results
```http
GET /api/v1/impact-analysis/{analysis_id}
```

#### Generate Test Plan
```http
POST /api/v1/test-plan/generate
Content-Type: application/json

{
  "analysis_id": "xyz789"
}
```

## 🔐 Security

### Key Security Features

- **OAuth2/JWT Authentication**: Secure user authentication
- **Input Validation**: Pydantic models for all API inputs
- **Prompt Injection Prevention**: Input sanitization and pattern blocking
- **Rate Limiting**: 100 requests per 15 minutes per IP
- **Secrets Management**: Environment variables, never committed
- **RBAC**: Role-based access control for sensitive operations

### Environment Variables

Required environment variables (see `.env.example`):

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Database
DB_USER=postgres
DB_PASSWORD=<secure-password>
MONGO_USER=admin
MONGO_PASSWORD=<secure-password>

# Security
JWT_SECRET=<secure-random-string>

# Application
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 📊 Monitoring & Observability

- **Structured Logging**: JSON format for all services
- **Health Checks**: `/health` endpoints for all services
- **Metrics**: Prometheus-compatible metrics
- **Dashboards**: Grafana dashboards (optional)

## 🧪 Testing Strategy

- **Unit Tests**: >80% code coverage target
- **Integration Tests**: Service-to-service communication
- **E2E Tests**: Complete user workflows
- **Security Tests**: Vulnerability scanning, prompt injection tests
- **Performance Tests**: Load testing with realistic scenarios

## 📈 Performance

- **Analysis Speed**: <30 seconds for typical repositories
- **Concurrent Users**: Supports multiple simultaneous requests
- **Caching**: Redis caching for dependency graphs and embeddings
- **Scalability**: Horizontal scaling via container orchestration

## 🎯 Use Cases

1. **Pre-Deployment Impact Analysis**: Assess risks before deploying changes
2. **Code Review Enhancement**: Understand full impact during reviews
3. **Test Optimization**: Focus testing on high-risk areas
4. **Technical Debt Assessment**: Identify highly coupled components
5. **Onboarding**: Help new developers understand system dependencies

## 🛠️ Troubleshooting

### Common Issues

**Service won't start**:
```bash
# Check logs
docker-compose logs <service-name>

# Rebuild container
docker-compose build --no-cache <service-name>
```

**Database connection errors**:
```bash
# Verify databases are running
docker-compose ps

# Check network connectivity
docker-compose exec api-gateway ping mongodb
```

**OpenAI rate limits**:
- Implement exponential backoff (built-in)
- Monitor token usage in logs
- Consider using GPT-3.5-turbo for non-critical operations

## 📝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Python: Follow PEP 8, use `black` formatter
- TypeScript: Follow Airbnb style guide
- Commit messages: Conventional Commits format

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Citi Impact Unplugged Hackathon
- LangChain and LangGraph communities
- OpenAI for GPT-4 API

## 📧 Contact

For questions or support, please open an issue in the GitHub repository.

---

**Built with ❤️ for the Citi Impact Unplugged Hackathon**
