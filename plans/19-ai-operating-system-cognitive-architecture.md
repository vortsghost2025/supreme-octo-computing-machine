# Planning Document 19: AI Operating System - 10-Agent Cognitive Architecture

## Goal
Evolve SNAC-v2 from a single runtime tool into an AI Operating System with specialized cognitive agents coordinated by an orchestrator and an event bus.

## Core Principle
Replace ad hoc task execution with role-based cognition.

User -> Cockpit -> Orchestrator -> Cognitive Agents -> Memory + Tools -> Event Bus -> Cockpit

## Agent Roles

1. Planner Agent
- Break goals into task graphs.
- Output: ordered task plan with dependencies.

2. Research Agent
- Gather evidence from web/docs/repos/papers.
- Output: sources, summaries, confidence.

3. Analyzer Agent
- Convert research into tradeoffs and implementation strategy.
- Output: pros, cons, risks, recommendation.

4. Idea Agent
- Generate expansion ideas and experiments.
- Output: new idea candidates routed into Thought Ingestion.

5. Builder Agent
- Produce implementation changes.
- Output: patch proposals and file edits.

6. Reviewer Agent
- Validate security, correctness, and architecture fit.
- Output: approve/reject with findings.

7. Tool Agent
- Perform environment actions: scripts, APIs, Docker ops.
- Output: execution receipts.

8. Memory Agent
- Maintain retrieval, linking, and graph consistency.
- Output: node/link updates and memory snapshots.

9. Monitor Agent
- Observe token, errors, latency, and health metrics.
- Output: alerts and thresholds.

10. Orchestrator Agent
- Dispatch and coordinate all agents.
- Output: global workflow state and next actions.

## Event Bus Requirement
Use Redis Pub/Sub first (already present), then upgrade to NATS if needed.

### Event Topics
- task.created
- task.planned
- research.completed
- analysis.completed
- idea.captured
- thought.ingested
- build.proposed
- review.completed
- deploy.started
- deploy.completed
- monitor.alert
- workflow.failed

### Event Envelope (JSON)
{
  "event_id": "uuid",
  "type": "task.created",
  "timestamp": "ISO8601",
  "session_id": "optional",
  "agent": "orchestrator",
  "payload": {},
  "trace_id": "uuid",
  "parent_event_id": "optional"
}

## Fit With Current State

Already present:
- Cockpit with timeline, node visualizer, token monitor
- Agent run API and timeline events
- Redis, Postgres, Qdrant in stack
- Thought Ingestion MVP with parse/classify/link behavior

Still missing:
- Dedicated orchestrator workflow state machine
- Real event bus contracts and publishers/subscribers
- Specialized agent modules (all 10 roles)
- n8n workflow bridge

## Phase Plan

### Phase 1: Event Bus Foundation (1-2 days)
- Add event publish helper in backend.
- Publish events for task lifecycle and thought ingest.
- Add simple event stream endpoint for cockpit consumption.

Definition of done:
- Timeline can be driven from event bus entries.
- All key actions emit typed events.

### Phase 2: Orchestrator Workflow Skeleton (2-3 days)
- Add orchestrator state machine: queued -> planning -> research -> build -> review -> deploy.
- Persist workflow instances in Redis and Postgres.
- Add retry/fail paths.

Definition of done:
- One user goal traverses complete orchestrated lifecycle.

### Phase 3: Cognitive Agent Split (4-6 days)
- Extract Planner, Research, Analyzer, Builder, Reviewer first.
- Use Tool Agent for system actions.
- Memory Agent records links and context.

Definition of done:
- Each role has explicit input/output contract.

### Phase 4: Cockpit Live Graph (2-4 days)
- Node visualizer reflects actual active agent path.
- Edge pulses based on live event updates.
- Add latest event feed panel with severity/status colors.

Definition of done:
- Cockpit feels alive with real-time progression.

### Phase 5: n8n Integration (2-3 days)
- Trigger n8n flows on event topics.
- Receive completion callbacks into orchestrator.
- Add no-code automation recipes.

Definition of done:
- External workflows become first-class actions in loops.

### Phase 6: Autonomous Dev Loop (3-5 days)
- Wire planner -> builder -> reviewer -> tool deploy loop.
- Add guardrails: approval gate, rollback, budget thresholds.

Definition of done:
- Controlled self-improvement loop can run on selected tasks.

## Immediate Build Order
1. Event bus publish utility
2. task.created + thought.ingested event emission
3. orchestrator workflow record model
4. planner/research/analyzer role stubs
5. cockpit event feed panel
6. n8n trigger endpoint

## Safety Guardrails
- Human approval required for deploy in production mode.
- Token and time budgets per workflow.
- Auto-stop after repeated review failures.
- Full audit trail: event + patch + reviewer decision.

## Key Metrics
- Plan quality score
- Build success rate
- Review rejection rate
- Mean time from idea to deployed change
- Cost per completed workflow

## 30-Day Target
By day 30, system should support:
- Thought -> structured project candidate
- Project candidate -> orchestrated execution plan
- Plan -> build/review/deploy loop with audit trail
- Live cockpit visibility over all stages
