# Plan 26: Core-5 Agent Loop Implementation

## Overview
Implement the Core-5 Agent system that orchestrates autonomous development workflows through permanent agent roles (Planner, Researcher, Builder, Reviewer, Operator) using ephemeral swarm workers for execution.

## Current State
- Backend: `s:\snac-v2\snac-v2\backend\main.py` (3666 lines)
- Existing swarm endpoints: `/swarm/task`, `/swarm/status`, `/swarm/workers/*`, `/swarm/events/*`
- Event system: Redis Streams + in-memory fallback
- Worker types: `research_worker`, `builder_worker`, `review_worker`, `analysis_worker`, `idea_worker`, `automation_worker`

## Architecture

### Agent Endpoints Prefix
All core agent endpoints under `/agents/{agent_name}/*`

### Core Agent Roles

| Agent | Role | Primary Action |
|-------|------|----------------|
| Planner | DAG/Task emit | Converts goals → project DAG + task trees |
| Researcher | Evidence harvest | Gathers docs, web, internal memory |
| Builder | Artifact creation | Produces code, config, infrastructure |
| Reviewer | Quality gate | Enforces security, quality, cost guardrails |
| Operator | Runtime control | Manages workers, deploys, verifies |

### Event Contract Schema
All agent coordination uses existing `_swarm_emit_event()` with typed payloads.

```
Topic families:
- agent.plan.created        # Planner emits DAG
- agent.task.created       # Task queued for workers
- agent.research.started   # Researcher begins gathering
- agent.research.complete  # Evidence bundle produced
- agent.build.started     # Builder begins implementation
- agent.build.complete    # Artifact produced
- agent.review.started    # Reviewer begins validation
- agent.review.gate       # Pass/fail decision
- agent.deploy.started    # Operator begins deployment
- agent.deploy.complete   # Deployment verified
- agent.cycle.complete    # Full loop complete
```

---

## Implementation Details

### 1. New Data Models (add to main.py ~line 860)

```python
# Agent-specific request/response models

class PlannerCreatePlanRequest(BaseModel):
    goal: Annotated[str, Field(min_length=1, max_length=4000)]
    context: Optional[Dict[str, Any]] = None
    constraints: Optional[List[str]] = None
    routing: str = "auto"  # auto, local_preferred, cloud_preferred
    
class PlannerCreatePlanResponse(BaseModel):
    plan_id: str
    dag: Dict[str, Any]  # Directed acyclic graph of tasks
    tasks: List[Dict[str, Any]]
    estimated_duration: int  # seconds

class PlannerTaskStatusRequest(BaseModel):
    plan_id: str
    
class PlannerTaskStatusResponse(BaseModel):
    plan_id: str
    status: str  # planning, researching, building, reviewing, deploying, complete, failed
    progress: Dict[str, int]  # {total, completed, failed, blocked}
    current_phase: str
    elapsed_seconds: int

class ResearcherGatherRequest(BaseModel):
    query: Annotated[str, Field(min_length=1, max_length=2000)]
    sources: List[str] = ["web", "docs", "memory"]  # web, docs, memory
    max_items: int = 10
    
class ResearcherGatherResponse(BaseModel):
    request_id: str
    evidence: List[Dict[str, Any]]
    confidence: float
    citations: List[str]

class BuilderCreateArtifactRequest(BaseModel):
    spec: Dict[str, Any]  # Task specification from Planner
    runtime: str = "shared"  # shared, sandbox
    language: Optional[str] = None
    
class BuilderCreateArtifactResponse(BaseModel):
    artifact_id: str
    files: List[Dict[str, Any]]  # {path, content, language}
    test_files: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class ReviewerValidateRequest(BaseModel):
    artifact_ids: List[str]
    gate_type: str = "standard"  # standard, strict, security
    review_focus: List[str] = ["quality", "security", "cost"]
    
class ReviewerValidateResponse(BaseModel):
    review_id: str
    decision: str  # pass, fail, conditional
    findings: List[Dict[str, Any]]
    required_fixes: List[Dict[str, Any]]
    severity_summary: Dict[str, int]

class OperatorDeployRequest(BaseModel):
    artifact_ids: List[str]
    runtime: str = "sandbox"  # sandbox, production
    verify: bool = True
    
class OperatorDeployResponse(BaseModel):
    deploy_id: str
    status: str  # deployed, verified, failed
    endpoints: List[str]
    verification_results: Dict[str, Any]

class AgentCycleStatusRequest(BaseModel):
    cycle_id: str
    
class AgentCycleStatusResponse(BaseModel):
    cycle_id: str
    status: str
    phase: str
    completed_agents: List[str]
    pending_agents: List[str]
    outcomes: Dict[str, Any]
```

---

### 2. Core Agent Endpoint Implementation

#### 2.1 Planner Endpoints (`/agents/planner/*`)

```
POST   /agents/planner/plan          - Create project DAG from goal
GET    /agents/planner/plan/{plan_id} - Get plan status
GET    /agents/planner/dag/{plan_id}  - Get full DAG visualization
POST   /agents/planner/expand        - Add tasks to existing plan
DELETE /agents/planner/plan/{plan_id} - Cancel plan
```

**Planner Logic:**
1. Receives goal → invokes LLM to decompose into DAG
2. DAG nodes = tasks with dependencies
3. Each task has: `id`, `type` (research/build/review), `depends_on`, `acceptance_criteria`
4. Emits `agent.plan.created` event with DAG
5. Auto-creates tasks in swarm queue based on task types

#### 2.2 Researcher Endpoints (`/agents/researcher/*`)

```
POST   /agents/researcher/gather     - Gather evidence for query
GET    /agents/researcher/result/{request_id} - Get research results
POST   /agents/researcher/ingest    - Ingest findings to memory
```

**Researcher Logic:**
1. Subscribes to `agent.task.created` events where `task.type == research`
2. Queries web via `websearch`, docs via RAG, memory via `/memory/search`
3. Produces structured evidence bundle with confidence scores
4. Emits `agent.research.complete` event

#### 2.3 Builder Endpoints (`/agents/builder/*`)

```
POST   /agents/builder/create       - Create artifacts from spec
GET    /agents/builder/artifact/{id} - Get artifact details
POST   /agents/builder/validate    - Validate artifact syntax
GET    /agents/builder/list         - List recent artifacts
```

**Builder Logic:**
1. Subscribes to `agent.task.created` events where `task.type == build`
2. Uses routing policy (local/cloud) based on complexity
3. Generates code files from spec
4. Creates associated test files
5. Emits `agent.build.complete` event with artifact metadata

#### 2.4 Reviewer Endpoints (`/agents/reviewer/*`)

```
POST   /agents/reviewer/validate    - Run quality/security gates
GET    /agents/reviewer/result/{review_id} - Get review results
POST   /agents/reviewer/approve     - Manual override approval
POST   /agents/reviewer/reject      - Manual rejection
```

**Reviewer Logic:**
1. Subscribes to `agent.build.complete` events
2. Runs gates: quality (lint, typecheck), security (secret scan), cost (estimate)
3. Emits `agent.review.gate` with pass/fail/conditional decision
4. Blocks promotion if `decision == fail`
5. Returns required fixes if conditional

#### 2.5 Operator Endpoints (`/agents/operator/*`)

```
POST   /agents/operator/deploy      - Deploy verified artifacts
GET    /agents/operator/deploy/{id} - Get deployment status
POST   /agents/operator/rollback   - Rollback deployment
GET    /agents/operator/status     - Get operator status
POST   /agents/operator/scale      - Manual worker scaling
GET    /agents/operator/cycles      - List completed cycles
```

**Operator Logic:**
1. Subscribes to `agent.review.gate` events where `decision == pass`
2. Executes deployment to target runtime
3. Runs verification checks if requested
4. Emits `agent.deploy.complete` event
5. Triggers memory update for cycle outcomes

---

### 3. Task Routing Logic

```
Planner creates DAG → Tasks queued to swarm

Task type → Worker mapping:
  research → research_worker (queue: normal)
  build    → builder_worker (queue: high for critical)
  review   → review_worker (queue: high)
  analyze  → analysis_worker (queue: normal)
  idea     → idea_worker (queue: low)

Routing decision (in task payload):
  - runtime: shared|sandbox|parallel_test
  - routing: auto|local_preferred|cloud_preferred
```

### 3.1 SNAC Agent Worker Mapping

Map your 20+ existing agents to task types for the Core-5 orchestration:

| Core Role | Task Type | Worker Agents |
|----------|---------|--------------|
| **Researcher** | research | agent-meta-monitor, agent-source-grounding, agent-who-data, agent-protocols |
| **Builder** | build | agent-builder, agent-code-reviewer, agent-orchestrator |
| **Reviewer** | review | agent-reviewer, agent-fact-checker, agent-self-healer |
| **Operator** | deploy | agent-azure-coordinator, agent-trust-router, agent-ide |
| **Analyzer** | analyze | agent-contradiction-detector, agent-claim-extractor, agent-source-verifier |
| **Specialized** | various | agent-openclaw, agent-medical-pipeline, agent-memory-coord, agent-nvidia |

**Full Agent Inventory:**
1. agent-builder
2. agent-orchestrator
3. agent-reviewer
4. agent-monitor
5. agent-self-healer
6. agent-fact-checker
7. agent-meta-monitor
8. agent-openclaw
9. agent-who-data
10. agent-protocols
11. agent-medical-pipeline
12. agent-trust-router
13. agent-ide
14. agent-nvidia
15. agent-azure-coordinator
16. agent-source-grounding
17. agent-contradiction-detector
18. agent-source-verifier
19. agent-claim-extractor
20. agent-memory-coord

**Worker Selection Logic:**
- Complex/Large → Run multiple workers in parallel
- Security-critical → Use fact-checker + reviewer together
- GPU-intensive → Route to agent-nvidia first
- Unknown → Default to agent-builder + agent-reviewer combo

**Agent Registration at Startup:**
- Each agent registers with the Core-5 via `/swarm/register`
- Core-5 maintains worker registry with capabilities
- Dynamic scaling: add/remove workers without code changes

---

### 4. Event Contract Definitions

#### 4.1 Agent Events

```python
# Emit via _swarm_emit_event()

# Planner emits
{
    "event_type": "agent.plan.created",
    "payload": {
        "plan_id": "uuid",
        "goal": "string",
        "dag": {...},
        "task_count": int,
        "estimated_duration": int
    }
}

# Worker completes task
{
    "event_type": "agent.task.completed",
    "payload": {
        "task_id": "uuid",
        "task_type": "research|build|review",
        "result": {...},
        "duration_seconds": int
    }
}

# Reviewer gate decision
{
    "event_type": "agent.review.gate",
    "payload": {
        "review_id": "uuid",
        "artifact_ids": [...],
        "decision": "pass|fail|conditional",
        "findings": [...],
        "block_promotion": bool
    }
}
```

---

### 5. Review Gate Enforcement

```python
# Gate configuration
REVIEW_GATES = {
    "quality": {
        "enabled": True,
        "checks": ["lint", "typecheck", "format"],
    },
    "security": {
        "enabled": True,
        "checks": ["secret_scan", "dependency_audit"],
    },
    "cost": {
        "enabled": True,
        "max_estimated": 100.0,  # USD
    }
}

# Gate enforcement in Builder/Reviewer
def _enforce_review_gates(artifact, gate_config):
    findings = []
    for gate, config in gate_config.items():
        if not config["enabled"]:
            continue
        # Run checks, collect findings
        if gate == "quality":
            findings.extend(_run_quality_checks(artifact))
        elif gate == "security":
            findings.extend(_run_security_checks(artifact))
        elif gate == "cost":
            findings.extend(_run_cost_check(artifact))
    
    # Decision logic
    critical = [f for f in findings if f["severity"] == "critical"]
    if critical:
        return {"decision": "fail", "findings": findings, "block_promotion": True}
    
    major = [f for f in findings if f["severity"] == "major"]
    if major:
        return {"decision": "conditional", "findings": findings, "block_promotion": False}
    
    return {"decision": "pass", "findings": findings, "block_promotion": False}
```

---

### 6. Memory Integration

```python
# After each cycle complete, store patterns

class AgentCycleMemory(BaseModel):
    cycle_id: str
    goal: str
    duration_seconds: int
    task_outcomes: Dict[str, str]  # task_id -> outcome
    review_findings: List[Dict]
    deploy_status: str
    patterns_learned: List[str]
    
# Endpoints
POST /memory/agent/cycle   # Store completed cycle
GET  /memory/agent/patterns # Get learned patterns
POST /memory/agent/ingest  # Ingest from any agent
```

Memory bank integration uses existing `/memory/share` and `/memory/search` endpoints.

---

### 7. Implementation Phases

#### Phase 1: Foundation (Week 1)
- [ ] Add new Pydantic models for all agent requests/responses
- [ ] Implement `/agents/planner/*` endpoints
- [ ] Implement Planner DAG generation logic

#### Phase 2: Worker Integration (Week 2)
- [ ] Add `/agents/researcher/*` endpoints
- [ ] Add `/agents/builder/*` endpoints  
- [ ] Integrate with existing swarm task queue
- [ ] Add event subscriptions for task completion

#### Phase 3: Review Gates (Week 2-3)
- [ ] Add `/agents/reviewer/*` endpoints
- [ ] Implement gate check functions (quality, security, cost)
- [ ] Implement block_promotion logic

#### Phase 4: Operator & Memory (Week 3)
- [ ] Add `/agents/operator/*` endpoints
- [ ] Implement deployment logic
- [ ] Add memory integration for cycles
- [ ] Connect all event contracts

#### Phase 5: Testing & Polish (Week 4)
- [ ] End-to-end cycle test
- [ ] Review gate configuration
- [ ] Memory pattern verification
- [ ] API documentation

---

### 8. API Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents/planner/plan` | POST | Create project DAG from goal |
| `/agents/planner/plan/{plan_id}` | GET | Get plan status |
| `/agents/planner/dag/{plan_id}` | GET | Get DAG visualization |
| `/agents/researcher/gather` | POST | Gather evidence |
| `/agents/researcher/result/{id}` | GET | Get research result |
| `/agents/builder/create` | POST | Create artifact |
| `/agents/builder/artifact/{id}` | GET | Get artifact |
| `/agents/reviewer/validate` | POST | Run review gates |
| `/agents/reviewer/result/{id}` | GET | Get review result |
| `/agents/operator/deploy` | POST | Deploy artifacts |
| `/agents/operator/deploy/{id}` | GET | Get deployment status |
| `/agents/operator/status` | GET | Operator status |
| `/memory/agent/cycle` | POST | Store cycle memory |

---

### 9. Configuration

```python
# Environment variables
CORE5_ENABLED = os.getenv("CORE5_ENABLED", "true")
CORE5_MAX_PLAN_TASKS = int(os.getenv("CORE5_MAX_PLAN_TASKS", "50"))
CORE5_DEFAULT_GATES = os.getenv("CORE5_DEFAULT_GATES", "quality,security,cost")
CORE5_AUTO_DEPLOY = os.getenv("CORE5_AUTO_DEPLOY", "false").lower() in {"1", "true"}
```

---

### 10. Verification Commands

```bash
# Health check
curl http://localhost:8000/agents/planner/health

# Create a plan
curl -X POST http://localhost:8000/agents/planner/plan \
  -H "Content-Type: application/json" \
  -d '{"goal": "Create a REST API for user management"}'

# Get plan status
curl http://localhost:8000/agents/planner/plan/{plan_id}

# Run research
curl -X POST http://localhost:8000/agents/researcher/gather \
  -H "Content-Type: application/json" \
  -d '{"query": "best practices for REST API design", "sources": ["web", "memory"]}'

# Create artifact
curl -X POST http://localhost:8000/agents/builder/create \
  -H "Content-Type: application/json" \
  -d '{"spec": {...}, "runtime": "sandbox"}'

# Run review
curl -X POST http://localhost:8000/agents/reviewer/validate \
  -H "Content-Type: application/json" \
  -d '{"artifact_ids": ["..."], "gate_type": "standard"}'

# Deploy
curl -X POST http://localhost:8000/agents/operator/deploy \
  -H "Content-Type: application/json" \
  -d '{"artifact_ids": ["..."], "runtime": "sandbox"}'

# Events
curl http://localhost:8000/swarm/events/recent?limit=30
```

---

### 11. Dependencies

- Existing `/swarm/*` endpoints for worker management
- Existing `_swarm_emit_event()` for event contracts
- Existing memory endpoints (`/memory/*`)
- Existing RAG system for researcher docs source

---

## Acceptance Criteria

1. **Planner** can decompose a goal into a DAG with 5+ tasks
2. **Researcher** can gather evidence from web + memory + docs
3. **Builder** can produce valid code artifacts from specs
4. **Reviewer** enforces all configured gates and blocks on failure
5. **Operator** can deploy and verify artifacts
6. **Event contracts** connect all agents via existing event system
7. **Memory** stores cycle outcomes and patterns
8. Full autonomous loop executes end-to-end without manual intervention
