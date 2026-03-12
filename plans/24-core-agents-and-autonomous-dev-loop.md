# Planning Document 24: Core-5 Agents, Autonomous Dev Loop, and Self-Building Cockpit

## Purpose
Translate the platform blueprint into an implementable operating model using 5 permanent agents plus ephemeral swarm workers.

## Core Design Rule
Permanent agents are stable control roles. Execution scale comes from temporary workers.

Permanent Core-5:
1. Planner
2. Researcher
3. Builder
4. Reviewer
5. Operator

## Role Contracts

## 1) Planner (Brain)
Responsibilities:
- Convert ideas into project DAGs.
- Convert goals into task trees with acceptance criteria.
- Route tasks to the right worker class.

Must not:
- Write production code directly.
- Execute deploy operations.

Outputs:
- Project manifest
- Task graph
- Priority schedule

## 2) Researcher (Knowledge Harvester)
Responsibilities:
- Gather external/internal evidence.
- Produce structured summaries with confidence and citations.
- Feed verified findings to memory graph.

Outputs:
- Evidence bundles
- Research summaries
- Knowledge candidates

## 3) Builder (Creator)
Responsibilities:
- Implement code/config/infrastructure artifacts.
- Produce tests and migration artifacts.
- Emit build telemetry and artifact metadata.

Routing policy:
- Simple tasks -> local model preferred.
- Complex tasks -> cloud model preferred.

## 4) Reviewer (Safety Net)
Responsibilities:
- Enforce security/quality/cost guardrails.
- Validate tests, architecture, and policy compliance.
- Block promotion on failure.

Outputs:
- Pass/fail gate decisions
- Findings with severity
- Required fix list

## 5) Operator (System Manager)
Responsibilities:
- Monitor runtime health, queue depth, worker load.
- Scale workers and manage deployment lifecycle.
- Execute rollback/recovery under policy controls.

Outputs:
- Runtime actions
- Deploy/verify records
- Incident events

## Swarm Worker Classes (Ephemeral)
- research_worker
- analysis_worker
- builder_worker
- review_worker
- automation_worker
- idea_worker

Worker lifecycle:
spawn -> claim -> execute -> publish -> retire

## Event-Driven Coordination
All coordination uses bus events only.

Required topic families:
- agent.task.created
- agent.task.started
- agent.task.completed
- agent.task.failed
- worker.spawned
- worker.retired
- guardrail.triggered

No direct cross-agent command chains in critical workflows.

## Autonomous Dev Loop
1. Planner emits DAG and tasks.
2. Research workers gather context.
3. Builder workers implement artifacts.
4. Reviewer validates and gates.
5. Operator deploys and verifies.
6. Memory updates patterns for future loops.

## Self-Building Cockpit Pattern
Goal: let the system improve its own cockpit safely.

Flow:
1. Planner creates cockpit improvement task.
2. Builder proposes patch in sandbox mode.
3. Reviewer runs security/regression checks.
4. Operator deploys only on pass.
5. Memory records outcome and lesson.

Safety requirements:
- No direct production mutation from shared mode.
- Reviewer and operator approvals required.
- Full audit trail on all self-build actions.

## Memory Graph Engine
Purpose: convert high-volume thoughts into executable structure.

Node types:
- idea
- project
- task
- result
- knowledge

Edge types:
- idea_to_project
- project_to_task
- task_to_result
- result_to_knowledge
- knowledge_to_task

Pipeline:
1. Ingest thought.
2. Classify domain and intent.
3. Cluster with related nodes.
4. Create or link project/task nodes.
5. Queue planner follow-up if confidence threshold passes.

## Dual Runtime Requirement
Every execution request declares runtime profile:
- shared
- sandbox
- parallel_test

Debug protocol:
1. Freeze shared run.
2. Replay task in sandbox.
3. Run N parallel replicas.
4. Compare outputs and traces.
5. Promote validated result.

## Definition of Done
- Core-5 contracts are implemented and enforced.
- Worker classes run through event bus only.
- Autonomous loop executes one full feature from plan to deploy.
- Self-building cockpit flow is functional in sandbox with guardrails.
- Memory graph links at least one thought to project->task->result path.
