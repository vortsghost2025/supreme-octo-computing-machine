# SNAC-v2 Project Review

## 1. Repository Overview

Root directory: `s:\snac-v2\snac-v2`

Primary language: Python (FastAPI backend) with React (frontend) and Docker support.

Key directories:
- `backend/`: Core API, RAG pipeline, memory timeline, swarm orchestration.
- `frontend/`: React cockpit UI, terminal emulation, visualization panels.
- `plans/`: Architectural roadmaps, scaling plans, deployment guides.
- `memory-bank/`: Session-level memory files (identity-signal.md, PHOENIX-PROTOCOL.md).
- `scripts/`: Automation scripts for deployment, diagnostics, and maintenance.
- `docker-compose.yml` & related files: Container orchestration for services (Redis, Qdrant, PostgreSQL, etc.).
- `nginx/`: Reverse-proxy configuration for UI and API services.

## 2. Core Components

| Component | Purpose | Key Technologies |
|-----------|---------|------------------|
| FastAPI Backend | REST/WS API, RAG, memory management | FastAPI, AsyncOpenAI, Qdrant, Redis (asyncio), PostgreSQL/ClickHouse (fallback) |
| Memory Timeline | Persistent storage of thoughts, events, and evolution | In-memory lists with Redis/Qdrant fallback; timeline events appended via `_timeline_append` |
| Swarm Orchestration | Agent lifecycle, scaling, health monitoring | Redis Streams for event bus, custom worker pool, health metrics |
| Terminal Fabric | Multi-shell access (CMD, PowerShell, Bash, WSL, Docker, SSH, K8s, cloud shells) | WebSocket-based terminal sessions, process management, capability packets |
| RAG Engine | Retrieval-augmented generation for knowledge retrieval | Qdrant vector search, embedding generation via OpenAI-compatible API |
| Cockpit UI | Visualization of agents, terminals, memory graph, task graph | React, WebSockets, D3/Vis.js for graph rendering |
| Event Contracts | Structured event schema for inter-component communication | `_EVENT_CONTRACTS` dictionary, validation via `_validate_event_contract` |
| Command Policy Engine | Risk classification and approval workflow for executing commands | Regex-based risk detection, audit logging, manual approval endpoints |

## 3. Infrastructure & Deployment

- **Containerization**: Docker Compose defines services for backend, frontend, Redis, Qdrant, and optional PostgreSQL/ClickHouse.
- **Orchestration**: `snac-v2.service` systemd-style script for process supervision.
- **Configuration**: Environment variables (`OPENAI_API_KEY`, `QDRANT_HOST`, `REDIS_HOST`, etc.) with fallback defaults.
- **Security**: Token-based control-plane access (`SNAC_OPERATOR_TOKEN`), secret redaction in logs, sandbox runtime policies.
- **Monitoring**: Token usage tracking, memory fallback pruning, swarm scaler metrics (`swarm_intelligence_stats`).

## 4. Key Functional Flows

**Idea Ingestion** – `ingest_document` and `ingest_thought` pathways parse input, chunk, embed, and store in Qdrant; also publish to Redis Streams for event propagation.

**Agent Execution** – `run_agent` parses compound tasks, spawns workers, executes steps, records results, and updates memory timeline.

**Swarm Event Flow** – Events travel via Redis Streams (`swarm:events:stream`), are validated, persisted, and consumed by workers; checkpointing supports crash recovery.

**Terminal Sessions** – Users create sessions (`/terminal/sessions`) that spawn shell processes; output streamed back via Server-Sent Events.

**Memory Management** – Fallback in-memory structures (`agent_sessions`, `memory_timeline`, `thought_memory`) are pruned when size limits (`_MEMORY_FALLBACK_MAX_*`) are exceeded.

## 5. Strengths

- **Modular Architecture**: Clear separation of concerns (API, memory, swarm, UI) with well-defined interfaces.
- **Scalable Event Bus**: Redis Streams + sharded idea streams enable horizontal scaling to 100k+ nodes.
- **Robust Safety Layer**: Command risk classification, sandbox policies, and operator token enforcement prevent accidental destructive actions.
- **Extensible Memory System**: Multi-layered storage (raw, semantic, graph) supports efficient retrieval and compression.
- **Comprehensive Documentation**: `plans/` directory contains detailed roadmaps, deployment guides, and scaling strategies.

## 6. Areas for Improvement / Open Tasks

### High Priority
- [x] **Swarm Cortex Bus Implementation**: Redis Stream sharding (swarm.ideas.0-31) - **IMPLEMENTED** (`backend/cortex_bus.py`)
- [x] **Hypersonic Idea Ingestion Pipeline**: Deduplication, semantic clustering, graph linking - **IMPLEMENTED** (`backend/hypersonic_pipeline.py`)
- [x] **Parallel Cognition Engine**: Agent forking and result merging - **IMPLEMENTED** (`backend/parallel_cognition.py`)

### Medium Priority
- [x] **Swarm Compression Engine**: Idea clustering and blueprint generation - **IMPLEMENTED** (`backend/compression_engine.py`)
- [ ] **Offline Swarm Mesh**: Bluetooth/Wi-Fi Direct integration not implemented.
- [ ] **Comprehensive Testing**: End-to-end scenario tests for high-volume idea ingestion and agent coordination are missing.

### Lower Priority
- [ ] **Performance Benchmarks**: Load testing for 20M+ ideas/day and 100k concurrent agents not yet performed.

## 7. Dependency & Risk Summary

- **External Services**: Relies on OpenAI-compatible embedding API and Qdrant; service availability impacts core functionality.
- **Resource Limits**: Memory fallback caps (`_MEMORY_FALLBACK_MAX_*`) must be tuned for expected workload; improper limits could cause OOM.
- **Security Surface**: Command approval flow and token handling need rigorous audit; current regex-based checks are a baseline.
- **Scalability Gaps**: Event consumer group coordination and back-pressure handling for Redis Streams are not fully stress-tested.

## 8. Conclusion

The SNAC-v2 codebase presents a sophisticated, event-driven architecture for a personal AGI-style operating system. Core services (FastAPI backend, Redis-backed event bus, Qdrant vector store, React cockpit) are well-structured and exhibit clear separation of concerns. The project already supports multi-shell terminal access, memory timeline tracking, and basic swarm orchestration. However, the full Swarm Cortex Stack—particularly the sharded idea streams, high-throughput ingestion pipeline, and compression mechanisms—remains to be implemented. Addressing the open tasks will be essential to achieve the targeted scale of 100k compute nodes and 20M+ ideas per day.

---

*Last Updated: 2026-03-13*
