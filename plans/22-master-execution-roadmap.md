# SNAC-v2 Master Execution Roadmap (01-21 + Cockpit IDE Program)

Updated: 2026-03-12
Owner: SNAC Program (Human + Agent Team)

---

## 0) Operating Truth and Non-Negotiables

1. Production runtime truth is Hostinger VPS Docker at `/opt/snac-v2/backend`.
2. Local Windows Docker is for development, repro, and validating changes before redeploy.
3. If SSH edits fail, do not rebuild locally as production. Fix in repo, commit, push, redeploy VPS.
4. Git root for this project is `S:/snac-v2/snac-v2`.

---

## 1) Program Snapshot

- Original scope (Plans 01-15): Foundation + cockpit observability + hardening + VPS launch path.
- Expansion scope (Plans 16-21): architectural analysis, cockpit redesign, 10-agent OS model, swarm scale-out, persistent memory bank.
- Current state: strong core platform, advanced feature growth, but production hardening and operations automation are still partially complete.

### Strategic Direction (Locked)
- Build around 5 permanent core agents and ephemeral swarm workers.
- Keep all cross-agent coordination event-driven through Redis contracts.
- Treat the cockpit as an AI OS surface: IDE + orchestration + memory + runtime control.

---

## 2) Roadmap Status Matrix (Plans 01-15)

| Plan | Theme | Status | Done Evidence | Remaining to Close |
|---|---|---|---|---|
| 01 | Initial architecture vision | Partial | Core stack and cockpit delivered | Align orchestration/security details with actual implementation |
| 02 | Architecture blueprint | Partial | Service layout largely present | Close observability + ops automation drift |
| 03 | Foundation build | Mostly complete | Compose + backend + UI are active | Formal orchestrator service split if still required |
| 04 | Critical fixes | Mostly complete | Safety and config fixes landed | Verify all originally listed edge cases in regression checks |
| 05 | SSL/Certbot | Partial | Nginx config and TLS notes present | Full cert lifecycle, renewals, validation, rollback |
| 06 | Cockpit panel v1 | Complete | Cockpit panel baseline active | Maintainability refactor as needed |
| 07 | Cockpit panel v2 | Complete | Enhanced cockpit controls active | UX polish and error state hardening |
| 08 | Memory timeline | Complete | Timeline events and UI present | Persist/retention strategy |
| 09 | Node visualizer | Complete | Node visualizer active | Advanced node-level telemetry |
| 10 | Ephemeral memory timeline | Complete | Ephemeral session flow active | Explicit lifecycle policies and retention guardrails |
| 11 | Token monitor | Complete | Cost monitor active | Model-aware dynamic pricing data source |
| 12 | Token monitor v2 | Complete | Refined monitor behavior active | Validation against real billing patterns |
| 13 | Production hardening | Partial | Baseline hardening in place | Timeout policies, stronger tool policy layer, full security closure |
| 14 | Launch path | Partial | Launch sequence documented | Full script-driven preflight/deploy/postflight automation |
| 15 | Hostinger deployment | Partial | VPS-first deployment model documented | Repeatable runbooks, rollback + recovery automation |

---

## 3) Additions Beyond Original 01-15 (Delivered)

### A) Cognitive and Swarm Additions
- Thought ingestion endpoint and cockpit action flow.
- Swarm phase-1 API surface (queue, status, scaler tick, events, config).
- Shared knowledge APIs and cockpit feed.
- Memory injection preview/apply APIs.
- Workflow learning endpoint for structured knowledge capture.

### B) Operational Additions
- Standalone repo isolation complete.
- VPS-first anti-rebuild guardrails documented in startup/handoff/readme.
- Local key-rotation scheduler implementation and audit logging.

### C) Strategic Additions (Docs 16-21)
- Comprehensive architecture analyses and redesign options.
- 10-agent cognitive architecture model.
- Self-expanding swarm program plan.
- Persistent memory bank architecture (48-layer concept).

---

## 4) Weak Spot Register (Current)

### Critical
1. Full production hardening closure is not complete.
2. SSL/cert operations are not fully automated end-to-end.
3. Launch/deploy/recover workflows remain too manual.
4. Event bus contracts are not yet formalized as versioned schemas and topic SLAs.

### High
1. Documentation drift still appears in some legacy planning assumptions.
2. Persistence strategy across timeline/swarm/knowledge needs explicit durability policy.
3. Incident response needs one-command diagnostics + runbook scripts.

### Medium
1. Cost governance should be model-aware and validated against observed spend.
2. Cockpit UX needs stronger degraded/offline signaling and retry UX.
3. Observability should evolve toward structured, queryable operational telemetry.

### Low
1. Build reproducibility can be improved with stricter image/dependency pinning.
2. Performance baselines and load envelopes should be continuously measured.

---

## 5) Full Improvement and Upgrade Backlog

## Security and Governance
- Complete TLS lifecycle and automated renewal checks.
- Add stronger API authn/authz patterns for future multi-agent command execution.
- Introduce command/tool policy engine (allow/deny/approval gates).
- Strengthen secret lifecycle and redaction controls.

## Reliability and Operations
- Add scripted preflight, deploy, postflight, rollback, and restore workflows.
- Add incident bundles (status, logs, health, queue state) as one-command outputs.
- Add failure-mode drills (backend down, redis down, qdrant degraded, nginx misroute).

## Data and Memory
- Define which events are ephemeral vs durable.
- Add persistence and retention policy by class (timeline, swarm events, learned memory).
- Add schema/version migration strategy for knowledge and memory models.

## Agent Runtime
- Expand from phase-1 swarm controls to full worker lifecycle management.
- Add role contracts for planner, builder, reviewer, ops, monitor.
- Add queue fairness and anti-starvation controls.
- Add versioned event bus contracts so agents communicate only through typed events.
- Implement planner-only task decomposition (planner never executes code directly).
- Add dynamic routing policy (`simple -> local`, `complex -> cloud`) for builder/reviewer execution.

## Cockpit UX
- Add disconnected/degraded status rail.
- Add replay/debug timeline mode.
- Add multi-pane command and agent coordination views.
- Continue accessibility optimization for low-vision fast operations.

## Delivery and Release
- Add CI validation gates (lint/test/build/security).
- Add release channels and rollback tags.
- Add VPS compatibility checks to every release candidate.

## Cost and Performance
- Move to dynamic model-aware cost accounting.
- Add budget policies per feature/agent.
- Add recurring load test baselines (P50/P95/P99).

## Event Bus Contracts
- Define canonical topic taxonomy (`swarm.task.created`, `swarm.worker.started`, `swarm.worker.finished`, `swarm.guardrail.triggered`, `timeline.event.appended`, `terminal.session.output`).
- Define payload schemas with required metadata (`event_id`, `trace_id`, `workflow_id`, `timestamp`, `source`, `version`).
- Add schema versioning and compatibility policy (`v1` additive-only changes).
- Add event retention and replay policy by topic class.
- Add dead-letter flow for invalid payloads and failed consumers.

---

## 6) Cockpit IDE Program (New Build Track)

Objective: Build a full IDE inside the cockpit that supports terminal powers (PowerShell, bash, cmd, sh), file operations, and multi-agent CLI collaboration.

### Design Principle: Dual-Mode Execution Is Mandatory

The platform must support both execution profiles through one control plane:

1. Shared Environment Mode
- Fast collaborative development.
- Multiple agents operate in one workspace and shared runtime.

2. Isolated Sandbox Mode
- Deterministic validation and tamper-resistant testing.
- Each agent runs in a separate sandbox runtime with reproducible inputs.

3. Parallel Test Mode
- Execute identical tasks across multiple isolated agents.
- Compare outputs to detect inconsistency, interference, or hallucination drift.

### Core-5 Agent Operating Model (Permanent Agents)

1. Planner
- Converts ideas/goals into project DAGs and executable task trees.
- Must not perform direct build/deploy actions.

2. Researcher
- Harvests docs/web/apis/internal memory.
- Produces structured evidence with citations and confidence.

3. Builder
- Produces code/config/infrastructure artifacts.
- Uses runtime routing to local vs cloud model based on complexity.

4. Reviewer
- Enforces quality and safety gates (security, logic, cost, architecture).
- Blocks promotion when guardrails fail.

5. Operator
- Manages runtime state (workers, queue depth, deploy, rollback, health).
- Owns promote/deploy decisions under approval policy.

All additional workers are ephemeral swarm workers spawned per task class.

### Runtime Switch Contract

Every task submission includes an explicit runtime profile:

```json
{
	"task": "generate API worker",
	"agent": "builder",
	"runtime": "shared"
}
```

or

```json
{
	"task": "generate API worker",
	"agent": "builder",
	"runtime": "sandbox"
}
```

Optional compare run:

```json
{
	"task": "generate API worker",
	"agent": "builder",
	"runtime": "parallel_test",
	"replicas": 3
}
```

Optional routing hint for model placement:

```json
{
	"task": "build endpoint tests",
	"agent": "builder",
	"runtime": "shared",
	"routing": "local_preferred",
	"complexity": "low"
}
```

## Core Capability Set
1. Multi-shell terminal tabs: PowerShell, bash, cmd, sh.
2. File workspace tools: explorer, open/edit, diff, patch apply preview.
3. Agent workspace board: spawn agents, assign tasks, track ownership/state.
4. Shared command bus: events, logs, tool outputs, approvals, and audit trail.
5. Human governance: approvals for risky/destructive command classes.
6. Runtime mode controls in cockpit: Shared, Sandbox, Parallel Test.
7. Replay controls: freeze shared run, replay in sandbox, compare outputs.
8. Core-5 control panel: planner/researcher/builder/reviewer/operator health and task ownership.
9. Thought ingestion panel with direct idea-to-project/task conversion.

## Reference Architecture
- Terminal Gateway: PTY session manager + websocket stream multiplexing.
- Command Policy Service: allowlist/denylist + approval workflow.
- Agent Coordinator: planner/worker/reviewer/ops state machine.
- Event Backbone: Redis streams/pubsub for task + result + telemetry.
- Cockpit IDE Frontend: terminal panes, files, board, timeline, approvals.
- Audit Store: immutable command/event ledger.

### Execution Controller (New Required Service)
- Sits between cockpit and runtime backends.
- Routes each task to shared or sandbox runtime.
- Enforces policy checks before command execution.
- Handles compare runs for `parallel_test` mode.

### Runtime Backends
- Shared Runtime Backend:
	- Common PTY sessions and shared project filesystem.
	- Used for rapid collaborative coding.
- Sandbox Runtime Backend:
	- One sandbox per agent run (container or namespace).
	- Input snapshot + limits + deterministic replay metadata.
	- Used for validation, debugging, and security-sensitive execution.

### Worker Classes (Ephemeral)
- research_worker
- analysis_worker
- builder_worker
- review_worker
- automation_worker
- idea_worker

Lifecycle: spawn -> claim task -> emit progress -> complete/fail -> retire.

## Security Model
- Least privilege by default.
- Session-scoped credentials and redaction.
- Command risk classes (safe, guarded, blocked).
- Signed audit events for forensics and trust.

### Command Risk Classes (Operational)
- `safe`: no approval required.
- `guarded`: approval required for production contexts.
- `dangerous`: explicit human approval + reason required.
- `blocked`: never executable from cockpit.

### Agent Capability Profiles
- Planner: read/plan, no destructive shell privileges.
- Builder: workspace edits + build/test commands.
- Reviewer: read/diff/test/lint, no deploy.
- Ops: deploy/restart/rollback with approval gates.
- Security: scanners, policy validation, audit tools.

## Multi-Agent CLI Collaboration Model
- Roles: Planner, Builder, Reviewer, Ops, Monitor, Memory.
- Workflow: Plan -> Execute -> Validate -> Approve -> Deploy -> Observe.
- Isolation: task branches/workspaces per agent.
- Convergence: reviewer gate before merge/deploy actions.

### Isolation Levels
1. Shared: no isolation, fastest iteration.
2. Workspace Snapshot: isolated filesystem snapshot, shared base runtime.
3. Full Sandbox: isolated container runtime per agent task.

### Debug and Integrity Flow
1. Freeze shared runtime for suspect task.
2. Replay the same task in sandbox.
3. Run N parallel isolated replicas.
4. Compare outputs and trace differences.
5. Promote only validated result back to shared flow.

### Autonomous Development Loop (Target)
1. Planner emits project DAG.
2. Research swarm gathers evidence.
3. Builder swarm produces artifacts.
4. Reviewer gates quality/security/cost.
5. Operator deploys and verifies.
6. Memory agent stores outcomes/patterns for next loop.

### Current Baseline (As of 2026-03-12)
- Swarm today is API + queue/event orchestration inside `backend/main.py`.
- Queueing and events are backed by Redis when available, with in-memory fallback.
- There is no separate long-running worker fleet or per-agent sandbox runtime yet.
- Immediate next build step is introducing the Execution Controller and worker runtime processes.

### 5 Core Agent Set (Platform Minimum)
1. Planner Agent
- Converts goals into executable DAG tasks and acceptance criteria.
2. Builder Agent
- Produces code/config changes and test artifacts.
3. Reviewer Agent
- Performs policy, quality, and regression review before promotion.
4. Ops Agent
- Handles deploy, verify, rollback, and runtime repair workflows.
5. Memory Agent
- Maintains learned knowledge, injection policy, and retrieval quality.

These five are sufficient to operate the full development loop end-to-end.

---

## 7) Milestone Checklist (With Owners and Validation)

| Milestone | Owner | Done Criteria | Validation Command(s) |
|---|---|---|---|
| M1 VPS Hardening Baseline | Ops Agent | TLS + proxy + security baseline active | `ssh root@187.77.3.56 "cd /opt/snac-v2/backend && docker compose ps"` |
| M2 Launch Automation | Ops + Builder | Preflight/deploy/postflight scripts operational | `bash scripts/launch-preflight.sh` |
| M3 Persistence Policy | Memory Agent | Durability and retention policy implemented | `curl -fsS http://localhost:8000/memory/timeline` |
| M4 Swarm Phase 2 | Planner + Swarm | Worker lifecycle + queue fairness active | `curl -fsS http://localhost:8000/swarm/status` |
| M5 Cockpit Reliability UX | UI Agent | Degraded/offline/error rails implemented | `npm --prefix ui run build` |
| M6 IDE Terminal MVP | IDE Agent | Multi-shell terminal sessions from cockpit | `pwsh -c "echo terminal-ok"` and `bash -lc "echo terminal-ok"` |
| M7 Execution Controller MVP | Coordinator + Runtime | Runtime switch (`shared`/`sandbox`) active for task submission | `curl -fsS http://localhost:8000/swarm/status` |
| M8 Multi-Agent CLI Orchestration | Coordinator Agent | Task board + multi-agent run + approval gates | `curl -fsS http://localhost:8000/swarm/events/recent` |
| M9 Parallel Integrity Testing | Runtime + Reviewer | Same task runs in N isolated replicas with output diff report | `curl -fsS http://localhost:8000/swarm/events/recent` |
| M10 Audit and Governance | Security + Ops | Command audit ledger + policy classes live | `curl -fsS http://localhost:8000/health` |
| M11 Event Contract Registry | Runtime + Security | Versioned event topics + schema checks enforced | `curl -fsS http://localhost:8000/swarm/events/recent` |
| M12 Core-5 Agent Loop | Coordinator + Team | Planner->Builder->Reviewer->Ops->Memory flow runs on one workflow DAG | `curl -fsS http://localhost:8000/swarm/status` |

Notes:
- Validation commands are baseline smoke checks and should be expanded per milestone.
- All production-impacting milestones require VPS-first verification and rollback steps.

---

## 8) 30-60-90 Day Execution Plan

## Day 0-30 (Stabilize + Harden)
- Close TLS/production hardening gaps.
- Ship launch automation scripts and runbooks.
- Remove stale doc drift; lock source-of-truth docs.
- Define persistence classes and retention policy.
- Lock Core-5 responsibilities and non-overlap rules.

## Day 31-60 (Scale + Operate)
- Implement swarm phase-2 worker lifecycle.
- Add structured observability and reliability dashboards.
- Introduce model-aware cost governance.
- Harden cockpit error/degraded UX.
- Ship event contract registry and topic schema validation.
- Bring researcher and builder worker classes online with queue fairness.
- Add idea-to-task planner transforms from thought ingestion.

## Day 61-90 (IDE + Multi-Agent)
- Deliver cockpit IDE terminal MVP.
- Deliver Execution Controller with shared/sandbox runtime switching.
- Add multi-agent CLI board and approval gates.
- Implement parallel isolated test mode with output compare.
- Implement command policy engine and immutable audit trail.
- Pilot end-to-end collaborative workflows (Planner->Builder->Reviewer->Ops).
- Promote full Core-5 loop with memory policy feedback closure.
- Enable self-building cockpit workflow behind reviewer/operator safeguards.

---

## 9) Decision Log (Live)

Use this section to log major program decisions as they happen.

| Date | Decision | Why | Impact | Owner |
|---|---|---|---|---|
| 2026-03-12 | VPS-first deployment truth locked | Prevent local rebuild confusion | Reduces operational drift and accidental rebuilds | Program |
| 2026-03-12 | SNAC isolated as standalone git repo | Eliminate parent-repo noise | Reliable git hygiene and review accuracy | Program |

---

## 10) Intake Placeholder (For Incoming User Notes)

Pending notes from user can be attached below and mapped to:
- Existing milestone updates
- New milestone requests
- Scope increases/decreases
- Risk register changes

## 11) Intake Integration (2026-03-12)

### User Direction Captured
- The system must support both shared and isolated agent execution modes.
- Isolation must be immediately available for debugging when shared execution looks inconsistent.
- Multiple CLI agents must be connectable and observable in one cockpit control plane.

### Design Decisions Added
1. Dual-mode runtime architecture is now mandatory (shared + sandbox).
2. Parallel test mode is required for deterministic comparison.
3. Execution Controller is now a first-class required service.
4. Runtime profile must be explicit per task and auditable.

### Open Technical Decision (Pending)
- Sandbox substrate choice for initial implementation:
	1. OS process/namespace isolation (faster to implement)
	2. Full Docker per-agent isolation (stronger security and reproducibility)
	3. Hybrid (process for quick tests, container for high-risk tasks)

Recommended initial path: Hybrid.

## 12) Distributed Compute Topology (Current and Target)

### Current Practical Topology
1. Local machine
- GPU-assisted ideation, coding, and cockpit interaction.
2. Hostinger VPS
- Primary runtime for backend agents, queueing, and platform APIs.
3. Optional burst tier (future)
- Additional worker capacity for heavy parallel jobs.

### Target Topology
- Keep control plane on VPS.
- Route heavy isolated test workloads to burst worker pool.
- Keep shared development loops close to local cockpit for speed.

## 13) Thought Ingestion Status

Thought ingestion is no longer missing conceptually.
- `POST /ingest-thought` exists and is part of current delivered capability.
- Next step is ranking, clustering, and project-tree auto-routing quality improvements.

### Memory Graph Engine (Next)
Goal: convert thought streams into structured graph entities.

Node types:
- idea
- project
- task
- result
- knowledge

Core edges:
- `idea -> project`
- `project -> task`
- `task -> result`
- `result -> knowledge`

Execution outcome: thoughts become executable project/task queues instead of unstructured backlog.

---

## 14) Crash-Proofing Intake (2026-03-12)

### Problem Statement (Captured)
- IDE/editor process resets must not cause task, worker, or context loss.
- Agent progress must be recoverable from durable state, not in-memory runtime state.

### Architecture Rule Added
- Runtime truth for task execution is now: `agent -> event bus -> persistent state`.
- VS Code is treated as an operator surface only, not a state store.

### Event Backbone Expansion (Required)
- Core streams:
	1. `swarm.tasks`
	2. `swarm.events`
	3. `swarm.results`
	4. `swarm.memory`
- Add `swarm.checkpoints` for long-running task resume metadata.

### Recovery Protocol (Required)
1. Worker boot sequence:
	- join consumer group
	- claim pending tasks
	- resume any task not marked completed
2. Task-level checkpoints:
	- periodic progress writes for long jobs
	- resume from last checkpoint index after restart
3. Backend restart flow:
	- replay recent streams
	- rebuild active queue + worker state
	- restart worker loops with pending claim/retry policy

### Cockpit Telemetry Endpoints (Required)
- `/swarm/graph/snapshot`
	- returns workers, running tasks, queue depth, active models, and graph edges for topology rendering
- `/swarm/intelligence/summary`
	- returns success rate, best worker, slowest task, and strategy recommendation

### Infrastructure Rule Added
- Core runtime components (backend, worker pool, Redis, vector db) must run outside the IDE process.
- Docker Compose is the default dev/prod orchestration boundary to survive editor restarts.

### Accessibility and Control Direction
- Favor low-navigation cockpit automation: voice command hooks, task templates, script shortcuts, high-signal telemetry rails.
- Automation must remain human-controllable through explicit policy/approval gates.

### Scale Pattern Captured
- Adopt recursive task decomposition for exponential swarm growth:
	- planner splits parent goal into task DAG
	- workers execute subtasks in parallel
	- merge and reviewer validation close the loop

