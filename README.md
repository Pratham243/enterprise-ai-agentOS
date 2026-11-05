# Enterprise AI AgentOS

**Multi-Agent Business Intelligence & Workflow Platform**

Enterprise AI AgentOS is a portfolio project built step by step into an enterprise-style AI platform. AI agents answer business questions, analyze data and documents, and automate workflows, with humans kept in the loop for important decisions.

> **202 tests passing** · All development steps complete · Production clients ready to configure

---

## Project Vision

A production-style **multi-agent AI platform** for **business intelligence** and **workflow automation** where specialized AI agents work together to:

- answer questions over company data and documents,
- run analytics and surface risks,
- trigger and coordinate business workflows,
- escalate decisions to humans when needed,

with full observability, evaluation, and enterprise deployment practices.

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| API | FastAPI + Uvicorn | Async backend REST API |
| Relational DB | PostgreSQL (SQLite for dev) | Structured business data and SQL analytics |
| Vector DB | Pinecone (in-memory for dev) | Document embeddings and semantic search for RAG |
| ORM | SQLAlchemy (async) + Alembic | Database models, queries, and versioned migrations |
| AI framework | LangGraph-style graph engine | Agent orchestration and conditional workflow graphs |
| Protocols | MCP | Standardized tool discovery and execution |
| ML | Rule-based (SHAP-ready) | Risk scoring with feature-level explainability |
| Evaluation | Heuristic scorer (MLflow-ready) | Response quality measurement |
| Automation | Webhook endpoints (n8n-ready) | External workflow triggers |
| Containers | Docker + Docker Compose | Packaging and local multi-service stack |
| Cloud | Azure (Terraform) | Production deployment |
| CI/CD | GitHub Actions | Automated testing pipeline |
| Frontend | React + Vite | Dashboard UI for all platform features |
| Observability | JSON logging + request tracing | Structured logs with request IDs for ELK/Datadog |
| Security | Rate limiting + headers + validation | API hardening against abuse and common web attacks |
| Real-time | WebSocket streaming | Live step-by-step agent workflow updates |
| Caching | In-memory (Redis-compatible) | TTL + LRU cache for LLM/RAG results |
| API Versioning | `/api/v1/` prefix router | Versioned endpoints with backward compatibility |
| Error Handling | Custom exception hierarchy | Structured JSON errors with codes and request IDs |
| Pagination | Offset-based with envelope | Paginated lists with total counts and filtering |
| Background Tasks | asyncio + in-memory manager | Fire-and-forget async jobs with status polling |
| RBAC | Role hierarchy + JWT claims | Admin/analyst/viewer endpoint protection |
| Throttling | Tiered rate-limit headers | Per-endpoint X-RateLimit-* response headers |
| Compression | GZip middleware | Automatic response compression for large payloads |
| OpenAPI | Enriched schema + examples | Professional Swagger UI with tag descriptions |
| Seed Data | Database seed script | Realistic demo data for immediate showcase |
| Frontend UX | Toast + Spinner + Dark/Light | Error toasts, loading spinners, theme toggle |

## Architecture

```
┌────────┐     ┌─────────────┐     ┌──────────────────┐     ┌──────────────┐     ┌──────────────┐
│  User  │ ──▶ │ Backend API │ ──▶ │ AI Orchestration │ ──▶ │    Agents    │ ──▶ │  Tools/Data  │
└────────┘     │  (FastAPI)  │     │  (Graph Engine)  │     │              │     │              │
               └─────────────┘     └──────────────────┘     │ Research     │     │ PostgreSQL   │
                     │                     │                 │ Analyst      │     │ Pinecone     │
                     │              ┌──────┴───────┐        │ Orchestrator │     │ ML Models    │
                     │              │  Conditional  │        └──────────────┘     └──────────────┘
                     │              │   Routing     │               │
     ▲               │              └──────────────┘               │
     │          ┌────┴────┐                                        │
     │          │  HITL   │  ◀── Human approves/rejects ──────────┘
     │          │ Gateway │
     │          └─────────┘
     └──────────────────────────── Response ◀──────────────────────┘
```

## API Endpoints

All business-logic endpoints are versioned under `/api/v1/`. Health probes stay at root level for Kubernetes and load balancers. Root-level (unversioned) routes remain available for backward compatibility.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Welcome message and docs link |
| GET | `/health` | Service health check (with uptime) |
| GET | `/health/live` | Liveness probe (Kubernetes) |
| GET | `/health/ready` | Readiness probe (dependency checks) |
| POST | `/api/v1/rag/ingest` | Ingest a document into the knowledge base |
| POST | `/api/v1/rag/query` | Search documents for relevant chunks |
| POST | `/api/v1/agent/query` | Route a question to the right agent |
| POST | `/api/v1/workflow/run` | Run the full graph orchestration pipeline |
| POST | `/api/v1/multi-agent/query` | Multi-agent orchestrator |
| GET | `/api/v1/mcp/tools` | Discover available MCP tools |
| POST | `/api/v1/mcp/execute` | Execute an MCP tool by name |
| POST | `/api/v1/approvals/` | Create a human-in-the-loop approval request |
| GET | `/api/v1/approvals/pending` | List pending approval requests |
| POST | `/api/v1/approvals/{id}/resolve` | Approve or reject a request |
| POST | `/api/v1/webhooks/trigger` | Receive webhook from automation platforms |
| POST | `/api/v1/risk/predict` | Risk scoring with explanations |
| POST | `/api/v1/evaluation/score` | Evaluate AI response quality |
| GET | `/api/v1/cache/stats` | Cache hit/miss statistics |
| POST | `/api/v1/cache/clear` | Flush cached results |
| POST | `/api/v1/audit/log` | Record an auditable event |
| GET | `/api/v1/audit/logs` | Paginated, filterable audit trail |
| POST | `/api/v1/tasks/submit` | Submit a background job (agent or workflow) |
| GET | `/api/v1/tasks/{id}` | Poll a task's status and result |
| GET | `/api/v1/tasks/` | List recent tasks (paginated) |
| GET | `/api/v1/tasks/stats` | Summary of task states |
| WS | `/api/v1/ws/agent` | Real-time streaming agent workflow |
| GET | `/docs` | Interactive Swagger UI documentation |

## Repository Structure

```
enterprise-ai-agentos/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── config.py            # Settings from environment
│       ├── exceptions.py        # Custom exception hierarchy
│       ├── error_handlers.py    # Global structured error handlers
│       ├── api/
│       │   ├── v1_router.py       # Versioned API router (/api/v1)
│       │   └── routes/            # All API endpoints
│       ├── agents/              # Agent system (research, analyst, orchestrator)
│       ├── tools/               # Agent tools (RAG, SQL)
│       ├── workflows/           # LangGraph-style graph engine
│       ├── services/            # RAG, risk model, evaluation, approvals, task manager
│       ├── models/              # SQLAlchemy ORM models
│       ├── mcp/                 # MCP tool registry
│       ├── db/                  # Database engine and session
│       └── migrations/          # Alembic versioned schema migrations
├── frontend/                    # React dashboard (Vite)
│   ├── src/
│   │   ├── components/          # Layout, sidebar
│   │   ├── pages/               # Dashboard, AskAgent, Documents, etc.
│   │   └── services/            # API client
│   └── vite.config.js
├── tests/                       # 202 automated tests
├── infrastructure/
│   └── main.tf                  # Terraform (Azure)
├── .github/workflows/
│   └── ci.yml                   # GitHub Actions CI pipeline
├── Dockerfile                   # Multi-stage production build
├── docker-compose.yml           # Local dev stack (API + PostgreSQL)
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Development Roadmap

| # | Stage | Status |
|---|---|---|
| 1 | Project foundation | ✅ Complete |
| 2 | FastAPI backend | ✅ Complete |
| 3 | PostgreSQL and SQL | ✅ Complete |
| 4 | Document intelligence and RAG (Pinecone) | ✅ Complete |
| 5 | AI agents and tools | ✅ Complete |
| 6 | LangGraph orchestration | ✅ Complete |
| 7 | Multi-agent architecture | ✅ Complete |
| 8 | MCP | ✅ Complete |
| 9 | Human-in-the-loop | ✅ Complete |
| 10 | Workflow automation (webhooks) | ✅ Complete |
| 11 | ML risk model | ✅ Complete |
| 12 | Evaluation | ✅ Complete |
| 13 | Docker | ✅ Complete |
| 14 | Azure deployment (Terraform) | ✅ Complete |
| 15 | CI/CD (GitHub Actions) | ✅ Complete |
| 16 | Production clients (LLM, embeddings, Pinecone, JWT) | ✅ Complete |
| 17 | Frontend dashboard (React + Vite) | ✅ Complete |
| 18 | Structured logging & observability | ✅ Complete |
| 19 | Rate limiting & API security hardening | ✅ Complete |
| 20 | WebSocket streaming (real-time agent) | ✅ Complete |
| 21 | Caching layer (LRU + TTL) | ✅ Complete |
| 22 | Database migrations (Alembic) | ✅ Complete |
| 23 | Health check dependencies & graceful shutdown | ✅ Complete |
| 24 | API versioning & OpenAPI documentation | ✅ Complete |
| 25 | Comprehensive error handling & custom exceptions | ✅ Complete |
| 26 | Pagination, filtering & audit log API | ✅ Complete |
| 27 | Background tasks & async job processing | ✅ Complete |
| 28 | Role-based access control (RBAC) | ✅ Complete |
| 29 | Request throttling & rate-limit headers | ✅ Complete |
| 30 | Response compression (gzip) | ✅ Complete |
| 31 | OpenAPI enrichment (examples, tags) | ✅ Complete |
| 32 | Database seeding & demo data | ✅ Complete |
| 33 | Frontend polish (toasts, spinner, dark/light mode) | ✅ Complete |

## Getting Started

### Local development (no Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run tests
python -m pytest tests/ -v

# Seed the database with demo data
python -m backend.app.seed

# Start the server
uvicorn backend.app.main:app --reload
# Open http://localhost:8000/docs
```

### With Docker

```bash
cp .env.example .env
docker compose up -d
# API at http://localhost:8000
# PostgreSQL at localhost:5432
```

### Deploy to Azure

```bash
cd infrastructure
terraform init
terraform plan -var="db_password=YOUR_SECURE_PASSWORD"
terraform apply
```

## Production Configuration

All production clients are built with automatic fallback to mocks. To activate them, set the appropriate environment variables in `.env`:

1. **LLM** — set `OPENAI_API_KEY` (or `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY`) to enable real GPT-4o calls
2. **Embeddings** — same key activates real `text-embedding-3-small` vectors
3. **Vector database** — set `PINECONE_API_KEY` + `PINECONE_INDEX_NAME` to use Pinecone instead of in-memory store
4. **Database** — set `DATABASE_URL` to a PostgreSQL connection string
5. **Authentication** — set `JWT_SECRET_KEY` to enable JWT-based API security
6. **Deploy** — run `terraform apply` in `infrastructure/`
