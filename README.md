# 🤖 Enterprise AI AgentOS - Multi-Agent Business Intelligence Platform

> **Production-grade multi-agent AI platform** combining RAG, SQL analytics, and autonomous tool-calling to automate complex enterprise workflows.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1-FF6F00?style=flat)](https://github.com/langchain-ai/langgraph)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen)](https://github.com/Pratham243/enterprise-ai-agentOS)

---

## What This Is

AgentOS is a deliberate shift from single-model scripts to enterprise AI software architecture. Instead of one LLM answering questions, it deploys a fleet of specialized business-domain agents that communicate autonomously, coordinate via protocols, and escalate to humans when needed.

**The core idea:** A user asks a natural-language business question → the orchestrator routes it to the right specialist agent → that agent uses RAG, SQL queries, or external tool calls to answer → results flow back through a typed response schema → n8n handles approval gates for any write operations.

---

## Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────┐
│   FastAPI Backend (REST API)    │
│   + PostgreSQL State Store      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│   LangGraph Orchestrator        │
│   (Agent Routing + State Graph) │
└────┬────────┬────────┬──────────┘
     │        │        │
     ▼        ▼        ▼
 RAG Agent  SQL Agent  Tool Agent
 (ChromaDB) (Postgres) (MCP calls)
     │        │        │
     └────────┴────────┘
             │
             ▼
        n8n HITL Gate
    (Human approval flows)
             │
             ▼
        Final Response
```

---

## Key Technical Decisions

| Decision | Rationale |
|---|---|
| **LangGraph over vanilla LangChain** | Explicit state graph enables conditional routing, retries, and debuggable agent traces |
| **MCP for external tools** | Standardized protocol keeps tool integrations modular and auditable |
| **A2A communication** | Agents delegate sub-tasks to peers rather than routing everything back to the orchestrator |
| **n8n for HITL** | Decouples approval logic from agent code; non-engineers can configure approval chains |
| **MLflow for eval** | Every agent call is logged; retrieval quality and generation metrics tracked per experiment |

---

## Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph, LangChain |
| Agent Protocols | Model Context Protocol (MCP), Agent-to-Agent (A2A) |
| Backend API | FastAPI, Python 3.11 |
| Database | PostgreSQL, ChromaDB (vector store) |
| LLM Provider | Azure OpenAI (GPT-4o) |
| Workflow Automation | n8n (HITL approval chains) |
| Experiment Tracking | MLflow |
| Explainability | SHAP |
| Infrastructure | Docker Compose, Terraform (planned) |
| CI/CD | GitHub Actions |

---

## Current Status

| Component | Status |
|---|---|
| FastAPI backend + PostgreSQL | ✅ Built |
| LangGraph orchestrator + agent routing | ✅ Built |
| RAG agent (ChromaDB + hybrid search) | ✅ Built |
| A2A agent communication | ✅ Built |
| MCP tool integration | ✅ Built |
| n8n HITL workflow automation | ✅ Built |
| MLflow experiment tracking | ✅ Built |
| Docker Compose local environment | ✅ Built |
| SHAP explainability on risk models | 🔄 In progress |
| Terraform + Azure cloud deployment | 🔄 In progress |
| Apache Spark data pipelines | 🔄 In progress |
| Apache Airflow scheduling | 🔄 In progress |

---

## How to Run (Local Dev)

```bash
git clone https://github.com/Pratham243/enterprise-ai-agentOS
cd enterprise-ai-agentOS
cp .env.example .env          # Add your Azure OpenAI keys
docker compose up --build     # Starts FastAPI + PostgreSQL + n8n
```

Then open `http://localhost:8000/docs` for the FastAPI Swagger UI.

---

## Why This Matters

Most AI portfolios show a chatbot or a single-model fine-tune. This project demonstrates:
- **System design** beyond a single model call
- **Production patterns**: typed schemas, async FastAPI, Dockerized deployment
- **Protocol-level thinking**: MCP and A2A, not just LangChain wrappers
- **Observability**: every agent run tracked in MLflow

---

*Started September 2026 · M.Sc. AI project @ BTU Cottbus · by [Prathamesh Shimpi](https://linkedin.com/in/prathamesh-shimpi0501)*
