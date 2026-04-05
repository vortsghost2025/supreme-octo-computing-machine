# Full Plan Audit — All 29 Documents vs Actual Codebase

**Date:** 2026-04-03
**Scope:** All 29 plan documents (4,500+ lines) cross-referenced against live codebase, Docker containers, and API endpoints

---

## Document Inventory

| Doc | Title | Lines | Core Theme |
|---|---|---|---|
| 01 | Initial Architecture Vision | 214 | 10-phase plan: server → agents → orchestration → RAG → tools → automation → UI → integrations → governance → scaling |
| 02 | Architecture Blueprint | 223 | Mermaid diagram, build order (11 days to MVP), folder structure, component map, timeline, improvement suggestions |
| 03 | Copy-Paste Foundation | 432 | docker-compose.yml, LangGraph+AutoGen+LlamaIndex code, Dockerfiles, smoke test |
| 04 | Critical Fixes | 58 | Redis port fix, OLLAMA env var, RAG caching, calculator sandboxing, n8n bind mounts |
| 05 | SSL/Certbot Config | 70 | Nginx SSL with auto-renewal, Mozilla Intermediate profile, certbot bootstrapper |
| 06 | Cockpit UI Panel | 47 | WebSocket-based cockpit with agent reasoning, tool traces, live logs, QUERY:/CALC: prefixes |
| 07 | Cockpit UI Panel v2 | 51 | State-synchronized UI, reverse-chronological tool timeline, memory trace visibility |
| 08 | Memory Timeline | 55 | Semantic memory tagging (RAG/TOOL/REASON/LOG), temporal visualization |
| 09 | Node Visualizer | 67 | LangGraph state machine debugger — Planner→Worker→END flow with pulse animations |
| 10 | Ephemeral Memory Timeline | 56 | Architecture-compliant: uses only existing LangGraph state, zero backend changes |
| 11 | Token Cost Monitor | 60 | Cost attribution by tool type, budget alerts at $4.00/$4.50 |
| 12 | Token Cost Monitor v2 | 54 | Refined v1 with same architecture-compliant approach |
| 13 | Production Hardening | 77 | 5-layer: NGINX throttling, OpenAI budget, timeouts, tool sandboxing, health checks |
| 14 | Launch Path | 128 | 25-minute zero-to-observable launch, 4 phases with verification |
| 15 | Hostinger VPS Deployment | 138 | Swap setup, Docker CE, UFW, Fail2Ban, budget guardrails |
| 16a | Comprehensive Analysis | 414 | Comparison of plans 01-15 vs codebase, weak points, 1000-agent roadmap, resource calculations |
| 16b | Unified Next.js Control Plane | 189 | Strategic pivot: one Next.js app on Hostinger, adapter pattern for external agents, session isolation |
| 17 | Cockpit Redesign Specs | 301 | Design spec: layout grid, color scheme, typography, component specs, animations, accessibility |
| 18 | Cockpit Visual Options | 113 | 3 options: Command Deck (calm), Ops Radar (dense), Focus Mode (guided) |
| 19 | AI OS Cognitive Architecture | 172 | 10-agent model: Planner, Research, Analyzer, Idea, Builder, Reviewer, Tool, Memory, Monitor, Orchestrator |
| 20 | Self-Expanding Agent Swarm | 199 | Dynamic swarm with queue pressure scaling, worker types, GTX 5060 local/cloud routing, 14-day plan |
| 21 | Persistent Memory Bank | 204 | 48-layer memory (6 domains × 8 layers), Postgres+Redis+Qdrant, injection policies, API contracts |
| 22 | Master Execution Roadmap | 533 | Status matrix for all plans, weak spot register, Core-5 agents, IDE program, 30-60-90 day plan |
| 23 | Event Bus Contracts | 158 | Versioned event envelopes, 19 topics, schema versioning, dead-letter handling, retention policy |
| 24 | Core-5 + Autonomous Dev Loop | 166 | Planner→Researcher→Builder→Reviewer→Operator, self-building cockpit pattern, memory graph engine |
| 25a | Crash Recovery Streams | 260 | Redis Streams dual-write, consumer groups, checkpoint protocol, boot recovery, intelligence accumulation |
| 25b | IDE Terminal Architecture | 1791 | PTY sessions, xterm.js, file workspace, agent board, command bus, policy engine, runtime modes |
| — | ARCHITECTURE-EVALUATION | 87 | 70% architecture complete, 50% deployed, 5/7 services running, missing nginx+n8n |

---

## IMPLEMENTATION STATUS — Every Plan vs Reality

### ✅ FULLY IMPLEMENTED

| Plan | What | Evidence |
|---|---|---|
| **06** Cockpit UI v1 | Memory Timeline, Node Visualizer, Token Monitor, Task Input, Ingest, Thought Input, Swarm Queue, Memory Learn, Memory Injection, Project Vault, Agent Chat, Free Coding Agent | `ui/src/App.jsx` — 1,962 lines, all panels present |
| **07** Cockpit UI v2 | State-synchronized UI, tool timeline, memory trace | Same App.jsx — all v2 features merged |
| **08** Memory Timeline | Semantic tagging, temporal visualization | `MemoryTimeline` component in App.jsx |
| **09** Node Visualizer | Planner→Worker→END flow, pulse animations | `NodeVisualizer` component in App.jsx |
| **10** Ephemeral Memory | Uses only existing state, zero backend | Timeline polls `/memory/timeline` — ephemeral |
| **11/12** Token Cost Monitor | Cost by session, budget bar, $4.00/$4.50 alerts | `TokenMonitor` component in App.jsx |
| **17** Cockpit Redesign | Color scheme, typography, grid, responsive | `ui/src/index.css` — 1,700+ lines with all vars |
| **18** Visual Options | Option C (Focus Mode) + Option A blend | Maximized inputs, large typography, modal controls |
| **21** Memory Bank APIs | POST /memory/learn, GET /memory/feed, POST /memory/share, POST /memory/inject/preview, POST /memory/inject/apply | 77 backend endpoints confirmed |
| **25a** Crash Recovery | Redis Streams dual-write, consumer groups, checkpoints, boot recovery, graph snapshot, intelligence summary | All endpoints live, `USE_REDIS_STREAMS=true` on VPS |
| **Governor** | 6 API endpoints, policy checks, UI panel, 29 tests | `backend/main.py` lines 5284-5330, `governor.ts` 316 lines |

### 🔶 PARTIALLY IMPLEMENTED

| Plan | What's Done | What's Missing |
|---|---|---|
| **01** Architecture Vision | Phases 1-7 largely delivered | Phases 8-10 (external integrations, governance, K8s scaling) not started |
| **02** Architecture Blueprint | Backend, frontend, Postgres, Redis, Qdrant running | n8n missing, orchestrator not separated as service |
| **03** Copy-Paste Foundation | docker-compose exists, backend+UI active | Orchestrator embedded in backend, not separate container |
| **04** Critical Fixes | Redis port fixed, calculator AST safety | n8n bind mount irrelevant (n8n not deployed) |
| **05** SSL/Certbot | Nginx directory exists | Not actively proxying — Traefik is the actual reverse proxy in Docker |
| **13** Production Hardening | Basic health checks, CALC sandboxing | NGINX throttling inactive, request timeouts not implemented, comprehensive tool allowlist missing |
| **14** Launch Path | System launches | No automated preflight/deploy/postflight scripts |
| **15** Hostinger VPS | VPS deployed at 187.77.3.56 | Swap config not automated, Fail2Ban not confirmed |
| **16a** Analysis | Weak points identified | 1000-agent roadmap not started |
| **16b** Unified Next.js | Current UI is Vite+React, not Next.js | Migration to Next.js not started |
| **19** AI OS (10 agents) | Thought ingestion, timeline events | No dedicated agent modules, no event bus contracts enforced |
| **20** Self-Expanding Swarm | Queue, status, scaler tick, events, config APIs | No dynamic worker lifecycle, no agent factory, no spawn/retire |
| **22** Master Roadmap | Core-5 defined, milestones listed | M1-M12 mostly not started |
| **23** Event Bus Contracts | `/events/contracts`, `/events/validate` endpoints | No versioned envelopes, no dead-letter stream, no schema validation |
| **24** Core-5 Dev Loop | Planner, researcher, builder, reviewer, operator endpoints exist | Not wired into actual autonomous loop — each is isolated endpoint |
| **25b** IDE Terminal | `IDETerminal.jsx` component exists, terminal session APIs | No WebSocket streaming, no xterm.js, no PTY, no file workspace |

### ❌ NOT STARTED

| Plan | What | Why It Matters |
|---|---|---|
| **05** SSL/Certbot (actual) | No real cert lifecycle | Exposed without proper TLS |
| **16b** Next.js Migration | Still Vite+React | Strategic direction says Next.js but not started |
| **19** Event Bus Foundation | No Redis Pub/Sub event routing | Agents can't coordinate through bus |
| **20** Agent Factory | No dynamic worker spawning | Swarm is API-only, no actual workers |
| **21** 48-Layer Memory | Only basic learn/feed/inject | No domain×layer matrix, no Postgres-backed entries |
| **22** M1-M12 Milestones | Only M6 (IDE Terminal) partially started | No VPS hardening baseline, no launch automation |
| **23** Schema Versioning | No envelope format enforcement | Events are ad-hoc JSON |
| **25b** File Workspace | No file explorer, diff/patch APIs | IDE terminal has no file operations |
| **25b** Agent Board | No task board UI | Swarm status is numeric only, no Kanban |
| **25b** Command Policy | Policy endpoints exist but no UI | No approval workflow in cockpit |
| **25b** Runtime Modes | No shared/sandbox/parallel switching | All execution is shared mode |

---

## LIVE DOCKER STATE (Verified 2026-04-03)

| Container | Status | Notes |
|---|---|---|
| `backend-backend-1` | Up 6 hours (healthy) | Port 8001→8000 |
| `snac-redis` | Up 6 hours | Port 6379 exposed |
| `snac-controller` | Up 5 hours | Orchestrator controller |
| `snac-orch-worker-1..4` | Up 6 hours | 4 swarm workers |
| `traefik-reverse-proxy` | Up 6 hours | Ports 80, 443, 8080 — **Traefik, not Nginx** |
| 6 web containers | Up 6 hours | Various domain sites |

**Key finding:** Traefik is the active reverse proxy, not Nginx. Nginx directory exists but is not routing traffic.

---

## BACKEND API ENDPOINTS (77 confirmed)

### Health & Status
- `GET /`, `/health`, `/api/health`, `/status`

### Ingestion
- `POST /ingest`, `/ingest-thought`, `/thoughts/ingest`
- `GET /thoughts/ranked`, `/thoughts/clusters`
- `POST /thoughts/to-project`

### Swarm
- `POST /swarm/task`, `/swarm/scaler/tick`, `/swarm/config`, `/swarm/workers/spawn`, `/swarm/workers/retire`, `/swarm/task/checkpoint`
- `GET /swarm/status`, `/swarm/events/recent`, `/swarm/results/recent`, `/swarm/graph/snapshot`, `/swarm/intelligence/summary`, `/swarm/workers`, `/swarm/workers/classes`, `/swarm/workers/{id}/lifecycle`
- `GET /swarm/task/checkpoint/{task_id}`

### Events
- `GET /events/contracts`, `/events/contracts/{type}`, `/events/contract-topics`
- `POST /events/validate`

### Policy
- `GET /policy/commands/classes`, `/policy/audit/log`
- `POST /policy/commands/classify`, `/policy/commands/approve`

### Memory
- `POST /memory/learn`, `/memory/share`, `/memory/workflow/learn`, `/memory/inject/preview`, `/memory/inject/apply`
- `GET /memory/feed`, `/memory/timeline`, `/memory/timeline/{session_id}`, `/memory/retention/policy`, `/memory/retention/stats`

### Agent
- `POST /agent/run`, `/free-coding-agent/run`
- `GET /free-coding-agent/tools`

### Tokens & Sessions
- `GET /tokens/usage`, `/session/{id}`
- `DELETE /session/{id}`

### Terminal
- `POST /terminal/sessions`, `/terminal/sessions/{id}/input`
- `GET /terminal/sessions/{id}`, `/terminal/sessions/{id}/output`
- `DELETE /terminal/sessions/{id}`

### Execution
- `POST /execute`
- `GET /execute/status/{id}`, `/execute`

### Core-5 Agents
- `POST /agents/planner/plan`, `/agents/researcher/gather`, `/agents/builder/create`, `/agents/reviewer/validate`, `/agents/operator/deploy`
- `GET /agents/planner/plan/{id}`, `/agents/planner/dag/{id}`, `/agents/researcher/result/{id}`, `/agents/builder/artifact/{id}`, `/agents/reviewer/result/{id}`, `/agents/operator/deploy/{id}`, `/agents/operator/status`

### Governor
- `GET /api/governor/context`, `/api/governor/search`, `/api/governor/guidance`
- `POST /api/governor/validate`, `/api/governor/narrate`, `/api/governor/refresh`

---

## GOOD IDEAS (Worth Keeping)

1. **Doc 16b: Unified Next.js Control Plane** — One deploy target, adapter pattern for external agents, session namespace isolation. Prevents split-stack fragility.

2. **Doc 16b §2.5: "Core Working Truth"** — "Repeated patterns across projects are not noise. They are evidence of recurring primitives." The cross-project primitive ledger (§9.6) is valuable.

3. **Doc 22: Dual-Mode Execution** — Shared + Sandbox + Parallel Test. The freeze→replay→compare debug protocol is solid engineering.

4. **Doc 25a: IDE Independence Rule** — "Cognitive state must not depend on any IDE session being alive." Critical and partially achieved with Redis-backed state.

5. **Doc 24: Self-Building Cockpit Pattern** — Builder proposes patch in sandbox → Reviewer validates → Operator deploys. Right safety model for self-modification.

6. **Doc 20: GTX 5060 Local/Cloud Routing** — Simple tasks to local model, complex to cloud. Cost-effective and practical.

7. **Doc 13: 5-Layer Hardening** — The layering approach (network → budget → timeout → sandbox → health) is correct even if not fully implemented.

8. **Doc 21: Memory Taxonomy** — 4 memory classes (event, execution, thought, strategy) with 3 storage tiers (Redis hot, Qdrant vector, Postgres durable) is the right abstraction.

---

## BAD IDEAS (Should Be Changed or Dropped)

1. **Doc 03: AutoGen + LangGraph + LlamaIndex all at once** — Doc 2 itself warns against this but Doc 3 does exactly it. The planner.py example calls `initiate_chat` inside a LangGraph node which will block. **Better**: Pick ONE orchestration pattern. Your current backend already has a working agent loop.

2. **Doc 02: 11-day MVP timeline** — Unrealistic for part-time. **Better**: Use Doc 16b's compression-horizon planning (North Star → This Week → Today → Now).

3. **Doc 21: 48-Layer Memory Bank** — 6 domains × 8 layers = 48 code paths. Premature abstraction. **Better**: Start with 4 memory classes and 2 tiers. Add layers only when you hit real conflicts.

4. **Doc 25b: 1,791-line terminal spec before MVP** — Thorough but you don't need a full IDE before you have a working terminal. **Better**: Phase 1 only — PTY session + WebSocket + xterm.js.

5. **Doc 02: Kubernetes migration path** — On a $5 VPS with 16GB RAM, K8s is overkill. **Better**: Docker Compose with resource limits is sufficient for 100+ agents with pooling.

6. **Doc 19: 10-Agent Cognitive Architecture** — Too many for current scale. **Better**: Doc 24's Core-5 is the right minimum. Add more only when Core-5 is bottlenecked.

---

## WHAT SHOULD CHANGE AND WHY

| Current Approach | Better Approach | Why |
|---|---|---|
| Split backend (FastAPI) + frontend (Vite React) | Migrate to Next.js unified (Doc 16b) | Single deploy target, eliminates CORS/proxy issues |
| Docker Compose monolith | Split infra/app compose files | Easier to restart infra without touching app |
| 48-layer memory | 4-class, 2-tier memory | 90% less complexity, covers all current use cases |
| 10-agent model | Core-5 + ephemeral swarm workers | Fewer permanent roles, scale from workers not roles |
| IDE terminal spec-first | Terminal MVP first, spec evolves | Discover what you actually need by using it |
| Manual VPS deployment | Scripted preflight/deploy/rollback | Eliminates human error, reproducible |
| Polling-based UI (2s intervals) | WebSocket or SSE for live updates | Reduces server load, instant updates |
| Nginx for reverse proxy | Keep Traefik (already running) | Traefik auto-discovers containers, handles TLS |

---

## THE BIGGEST GAP

**Doc 16b (Unified Next.js Control Plane) is the strategic north star but nothing has moved toward it.** Everything else — swarm, memory, agents, terminal, Governor — is building on top of a Vite+React + FastAPI split that the plan itself says should be migrated. Every feature added to the current stack increases the migration cost.

The Governor is a good candidate for the first Next.js migration target — self-contained, clear API contracts, single UI component.

---

## PRIORITY RECOMMENDATION

### Do Now (This Week)
1. Keep Traefik as reverse proxy (drop Nginx SSL plan — already solved)
2. Script VPS deploy/rollback (eliminate manual rebuild confusion)
3. Migrate one panel to WebSocket (start with Memory Timeline)

### Do Next (This Month)
4. Implement Core-5 agent loop (wire existing endpoints into actual workflow)
5. Add shared/sandbox runtime switching (Doc 22 dual-mode)
6. Build terminal MVP (PTY + WebSocket + xterm.js only)

### Defer (Not Yet)
- Next.js migration (wait until Core-5 loop is stable)
- 48-layer memory (start with 4 classes)
- 10-agent model (Core-5 is enough)
- Kubernetes (Docker Compose scales further than you think)
- n8n (you have Redis queues + event endpoints — use those first)
