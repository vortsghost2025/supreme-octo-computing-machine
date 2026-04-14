# SNAC-v2 Architecture & Implementation Plan

## Current State (April 7, 2026)

### What's Running on VPS (187.77.3.56)

| Container | Status | Purpose |
|-----------|--------|---------|
| snac_backend | ✅ Running (5,502 lines) | Main API, LLM, RAG, memory |
| snac_frontend | ✅ Running | React UI |
| snac_nginx | ✅ Running | Reverse proxy |
| snac_db | ✅ Running | PostgreSQL |
| snac_redis | ✅ Running | Cache |
| snac_qdrant | ✅ Running | Vector DB |
| kilo-gateway | ✅ Running | WebSocket hub (6 agents connected) |
| agent-orchestrator | ⚠️ Stub | Just registers, no logic |
| agent-builder | ⚠️ Stub | Just registers, no logic |
| agent-reviewer | ⚠️ Stub | Just registers, no logic |
| agent-monitor | ⚠️ Stub | Just registers, no logic |
| agent-nvidia | ⚠️ Stub | Just registers, no logic |
| agent-azure-coordinator | ⚠️ Stub | Just registers, no logic |
| snac_fact_checker | ✅ Running | Fact checking service |

---

## The Problem

**Agents are stubs** - They register to kilo-gateway but have no actual functionality.

Each agent has ~21 lines:
```python
@app.get("/health")
async def health():
    return {"status": "ok"}

async def register():
    uri = "ws://kilo-gateway:3002"
    async with websockets.connect(uri) as ws:
        await ws.send({"type": "register", "name": os.getenv("AGENT_NAME", "agent-xxx")})
```

---

## What Each Agent Should Do (Based on Names)

### 1. agent-orchestrator
**Purpose:** Coordinate multi-agent workflows, task delegation
**Backend endpoints:**
- `/agent/run` - Run agent tasks
- `/agents/planner/plan` - Create execution plans

### 2. agent-builder  
**Purpose:** Generate code, artifacts, files
**Backend endpoints:**
- `/agents/builder/create` - Create code artifacts
- `/agents/builder/artifact/{artifact_id}` - Retrieve artifacts

### 3. agent-reviewer
**Purpose:** Code review, validation, quality gates
**Backend endpoints:**
- `/agents/reviewer/validate` - Validate code/responses
- `/agents/reviewer/result/{review_id}` - Get review results

### 4. agent-monitor
**Purpose:** System monitoring, health checks, metrics
**Backend endpoints:**
- `/api/health` - Health monitoring
- Swarm status endpoints

### 5. agent-nvidia
**Purpose:** GPU workloads, local Ollama inference coordination
**Backend endpoints:**
- Uses local Ollama on the machine running this agent

### 6. agent-azure-coordinator
**Purpose:** Coordinate Azure AI services
**Backend endpoints:**
- `/agents/operator/deploy` - Deploy to Azure

---

## Backend API (snac_backend)

### Key Endpoints

**Core:**
- `POST /agent/run` - Run a task
- `POST /execute` - Execute code
- `GET /execute/status/{execution_id}` - Check execution status

**Memory:**
- `GET /memory/timeline` - Get memory events
- `POST /memory/inject/preview` - Preview memory injection
- `POST /memory/inject/apply` - Apply memory injection

**Swarm:**
- `POST /swarm/task` - Create swarm task
- `GET /swarm/status` - Get swarm status

**RAG:**
- `POST /rag/ingest` - Ingest documents
- `POST /rag/search` - Search documents

**Agent Endpoints:**
- `/agents/planner/plan` - Plan agent execution
- `/agents/researcher/gather` - Research task
- `/agents/builder/create` - Build artifacts
- `/agents/reviewer/validate` - Review/validate

---

## UI Integration Points

### Current UI (ui/src/App.jsx)
- **API_BASE:** `http://localhost:9002` (local dev) or proxied in production
- **Key functions:**
  - `runAgentTask(task)` → POST `/agent/run`
  - `fetchTimeline()` → GET `/memory/timeline`
  - `fetchSwarmStatus()` → GET `/swarm/status`
  - `handleTaskSubmit(task)` → User input to agent

### What's Missing in UI
1. No agent selector (which agent to use)
2. No swarm visualization
3. No RAG/document management
4. No code execution interface
5. No artifact management

---

## Connection Paths

```
User Browser
    ↓
Nginx (port 80/443)
    ↓
Frontend (:3000) ← serves UI
Backend (:8000) ← API calls
    ↓
Kilo-gateway (:3002) ← WebSocket
    ↓
Agents ( stubs registered )
```

---

## Implementation Plan

### Phase 1: Get UI Working
1. ✅ Backend running on VPS
2. ✅ Frontend running on VPS  
3. ⚠️ UI points to localhost:9002 (needs fix)
4. Fix UI to call VPS backend via nginx proxy

### Phase 2: Connect Agents to Backend
1. Implement agent-orchestrator to call `/agent/run`
2. Implement agent-builder to call `/agents/builder/create`
3. Implement agent-reviewer to call `/agents/reviewer/validate`
4. Implement agent-monitor to call `/api/health`
5. Implement agent-nvidia for local Ollama
6. Implement agent-azure-coordinator for Azure deployments

### Phase 3: Enhance UI
1. Add agent selector
2. Add swarm visualization
3. Add RAG management
4. Add artifact browser

### Phase 4: Production
1. Set up domain (snac.deliberatefederation.cloud)
2. Configure TLS/SSL
3. Set up monitoring

---

## Files to Modify

### Local (for development)
- `ui/.env` - Change VITE_API_URL
- `ui/src/App.jsx` - Add missing features

### VPS Agents (implement logic)
- `services/agent-orchestrator/main.py`
- `services/agent-builder/main.py`
- `services/agent-reviewer/main.py`
- `services/agent-monitor/main.py`
- `services/agent-nvidia/main.py`
- `services/agent-azure-coordinator/main.py`

---

## DNS/Domains Available

You mentioned 5 domains on Hostinger. Current nginx config expects:
- `snac.deliberatefederation.cloud` (already configured in nginx.conf)

We can add more subdomains for different services.
