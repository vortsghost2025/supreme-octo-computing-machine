# Planning Document 20: Self-Expanding Agent Swarm

## Objective
Turn SNAC-v2 into a dynamic swarm platform that spawns and retires specialized worker agents based on queue pressure, cost budgets, and system health.

## Design Rule
Agents never communicate directly.
All communication is event-driven through the bus.

## End-State Topology
Cockpit UI -> API Gateway -> Event Bus -> Orchestrator -> Agent Factory -> Worker Swarm -> Memory Graph -> Automation (n8n)

## Current Baseline
Already available:
- FastAPI backend
- Redis service
- Cockpit timeline/node/token panels
- Thought ingestion endpoint and timeline eventing

Missing for swarm:
- Task queue abstraction
- Dynamic worker lifecycle manager
- Orchestrator scheduler logic
- Event contracts enforced in code
- Spawn/rate/token guardrails

## Swarm Components

1. Swarm Orchestrator
- Reads queue depth + active workers + budgets.
- Decides spawn/scale-down actions.
- Emits lifecycle events.

2. Task Queue
- Redis-backed queue with priorities.
- Supports delayed retries and dead-letter routing.

3. Agent Factory
- Creates worker runtime contexts by role.
- Registers worker metadata and lease.

4. Worker Runtime
- Pulls one task, executes, emits result, updates memory, exits or returns to pool.

5. Memory Bridge
- Stores outputs as structured memory nodes and links.

6. Swarm Monitor
- Tracks worker health, queue lag, token burn, task SLA.

## Worker Types (Initial)
- planner_worker
- research_worker
- analyzer_worker
- builder_worker
- reviewer_worker
- idea_worker

## Queue and Event Model

### Redis Keys (MVP)
- swarm:queue:high
- swarm:queue:normal
- swarm:queue:low
- swarm:workers:active
- swarm:workers:leases
- swarm:deadletter

### Event Topics
- swarm.task.created
- swarm.task.started
- swarm.task.completed
- swarm.task.failed
- swarm.worker.spawned
- swarm.worker.stopped
- swarm.scaler.decision
- swarm.guardrail.triggered

### Event Envelope
{
  "event_id": "uuid",
  "type": "swarm.task.created",
  "timestamp": "ISO8601",
  "workflow_id": "uuid",
  "task_id": "uuid",
  "agent_type": "research_worker",
  "priority": "normal",
  "payload": {},
  "trace_id": "uuid"
}

## Scaling Algorithm (MVP)
Inputs:
- queue_depth_total
- active_workers
- max_workers
- cpu_percent
- tokens_per_min

Rule set:
- desired_workers = ceil(queue_depth_total / 2)
- clamp desired_workers between min_workers and max_workers
- if cpu_percent > 80 or tokens_per_min > budget_tpm -> freeze scale-up
- if queue_depth_total == 0 for idle_timeout -> scale down to min_workers

Recommended initial limits:
- min_workers: 2
- max_workers: 12
- max_tokens_per_min: 80000
- max_cpu_percent: 80

## GTX 5060 Local Reasoning Strategy
Use local model roles to reduce cloud cost.

Local first (Ollama or LM Studio):
- summarization
- classification
- embeddings
- routine planning drafts

Cloud fallback:
- high-stakes reasoning
- difficult code synthesis
- final review on risky diffs

Routing policy:
- if task_complexity <= medium and local queue healthy -> local model
- else -> cloud model

## API Contracts to Add

1. POST /swarm/task
- Submit a task into swarm queue.

2. GET /swarm/status
- Queue depth, active workers, guardrail state.

3. POST /swarm/scaler/tick
- Manual scaler trigger for testing.

4. GET /swarm/events/recent
- Recent swarm events for cockpit feed.

5. POST /swarm/config
- Update runtime limits (max workers, token budget, cpu threshold).

## Cockpit Upgrades

1. Swarm Monitor Panel
- active workers by type
- queue depth by priority
- spawn/retire chart
- guardrail status

2. Live Agent Map
- nodes appear/disappear by worker lifecycle events
- edges pulse on task handoffs

3. Event Feed
- structured activity stream with severity tags

## Safety and Control
- hard cap worker count
- hard cap token/min and token/day
- deploy actions require approval gate
- dead-letter queue for repeated failures
- circuit breaker for external tools

## 14-Day Execution Plan

Day 1-2:
- Implement queue abstraction and event publisher
- Add /swarm/task and /swarm/status

Day 3-5:
- Implement worker lease registry + scaler tick logic
- Add spawn/stop lifecycle events

Day 6-8:
- Add first 2 worker types (research, analyzer)
- Store outputs in memory bridge

Day 9-11:
- Add cockpit swarm monitor and live event feed
- Add worker node rendering in visualizer

Day 12-14:
- Add guardrails + dead-letter flow
- Add local-model routing policy hooks

## Definition of Done (MVP)
- Can submit 20+ queued tasks
- Scaler spawns workers up to cap
- Workers complete tasks and publish results
- Cockpit shows live worker lifecycle
- Guardrails prevent runaway expansion

## Stretch Goal
Enable autonomous dev loop jobs to execute through swarm under approval gates.
