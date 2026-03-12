# Planning Document 23: Event Bus Contracts and Runtime Messaging

## Purpose
Define strict, versioned event contracts so agents and services communicate through the bus without direct coupling.

## Principles
1. No direct agent-to-agent RPC for workflow coordination.
2. All cross-agent coordination must flow through typed events.
3. Every event must be traceable, replayable, and schema-validated.
4. Backward compatibility is required for additive changes.

## Transport and Topics
Transport: Redis Streams (primary), in-memory fallback for local dev only.

Core topics:
- swarm.task.created
- swarm.task.claimed
- swarm.task.started
- swarm.task.progress
- swarm.task.finished
- swarm.task.failed
- swarm.worker.started
- swarm.worker.stopped
- swarm.scaler.decision
- swarm.guardrail.triggered
- terminal.session.started
- terminal.session.input
- terminal.session.output
- terminal.session.error
- timeline.event.appended
- memory.entry.created
- memory.injection.previewed
- memory.injection.applied

## Envelope Contract (Required for all topics)

```json
{
  "event_id": "uuid",
  "event_type": "swarm.task.created",
  "event_version": "v1",
  "timestamp": "2026-03-12T12:00:00Z",
  "trace_id": "uuid",
  "workflow_id": "uuid",
  "task_id": "uuid",
  "source": "planner-agent",
  "runtime": "shared",
  "payload": {}
}
```

Required fields:
- event_id
- event_type
- event_version
- timestamp
- trace_id
- source
- payload

Optional by topic:
- workflow_id
- task_id
- runtime
- priority
- policy_decision

## Topic Payload Contracts

## 1) swarm.task.created

```json
{
  "task": "generate API worker",
  "agent_type": "builder",
  "priority": "normal",
  "complexity": "medium",
  "runtime": "shared"
}
```

## 2) swarm.task.finished

```json
{
  "status": "success",
  "duration_ms": 12450,
  "artifacts": ["backend/worker.py"],
  "summary": "worker created",
  "cost_usd": 0.023
}
```

## 3) swarm.guardrail.triggered

```json
{
  "guardrail": "dangerous_command",
  "decision": "blocked",
  "command": "rm -rf /",
  "reason": "blocked pattern"
}
```

## 4) terminal.session.output

```json
{
  "session_id": "uuid",
  "stream": "stdout",
  "chunk": "build complete",
  "sequence": 422
}
```

## Schema Versioning Policy
1. `v1` allows additive fields only.
2. Removing or renaming required fields requires `v2`.
3. Producers must include `event_version`.
4. Consumers must ignore unknown fields.

## Ordering and Idempotency
1. Ordering guaranteed only within stream partition.
2. Consumers must dedupe by `event_id`.
3. Handlers should be idempotent by design.

## Retention and Replay
1. High-value audit topics retain 30 days minimum.
2. Operational noise topics retain 3-7 days.
3. Replay tools must support trace_id and workflow_id filtering.

## Dead Letter Handling
1. Invalid payloads are routed to `deadletter.events`.
2. Dead letter records include parse/validation error metadata.
3. Dashboard must expose dead letter count and recent samples.

## Security and Policy Integration
1. Event integrity check: source identity and signed metadata when available.
2. Sensitive payload fields must be redacted before persistence.
3. Policy decision events must include actor and reason.

## Validation and Conformance
1. Producer-side schema validation before publish.
2. Consumer-side schema validation before process.
3. Contract tests in CI for all critical topics.

## Initial Implementation Checklist
1. Add shared envelope model in backend.
2. Migrate existing swarm event emission to envelope format.
3. Add runtime field (`shared` or `sandbox`) to task events.
4. Add deadletter stream and counters.
5. Add basic event contract test suite.

## Definition of Done
- All swarm and terminal events use versioned envelope.
- Invalid events are captured in deadletter stream.
- Event replay works by trace_id and workflow_id.
- Contract test suite passes in CI.
