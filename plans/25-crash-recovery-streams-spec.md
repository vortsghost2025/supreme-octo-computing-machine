# Plan 25: Crash Recovery, Redis Streams, and Persistent State Engine

## Purpose
Define the runtime model for survivable task execution. Covers Redis Streams dual-write, consumer group protocol, task checkpointing, worker boot recovery, worker intelligence accumulation, and the IDE-independence rule.

---

## 1. Event Bus Rule

Every event emitted by the swarm (task dispatched, completed, failed, memory stored, worker started) is written to two places simultaneously:
- **Redis List** (`swarm:events`) — fast FIFO tail for live UI polling (capped via ltrim)
- **Redis Stream** (`swarm:events:stream`) — append-only audit log, replayable, survives restart

This dual-write is implemented in `_swarm_emit_event`. The Streams path gates on `_USE_REDIS_STREAMS` env flag.

---

## 2. Redis Streams Architecture

### Streams Used

| Stream Key | Populated By | Consumer Group | Purpose |
|---|---|---|---|
| `swarm:events:stream` | `_swarm_emit_event` | `swarm-workers` | Event audit log + replay |
| `swarm:results:stream` | `_swarm_store_result` | `swarm-workers` | Result replay + second brain feed |
| `swarm:checkpoints` | `_swarm_checkpoint_write` | — (Redis hash, not stream) | Task progress snapshots |

### Consumer Group Setup

On lifespan startup:
```python
await _redis.xgroup_create("swarm:events:stream", "swarm-workers", id="0", mkstream=True)
await _redis.xgroup_create("swarm:results:stream", "swarm-workers", id="0", mkstream=True)
```
Errors from pre-existing groups are silently swallowed (BUSYGROUP is expected).

### XADD Pattern

```python
# In _swarm_emit_event:
await _redis.xadd(
    "swarm:events:stream",
    {"type": event_type, "payload": json.dumps(payload), "ts": str(now)},
    maxlen=_SWARM_STREAM_MAX_LEN,
    approximate=True,
)
```
`maxlen` with `approximate=True` keeps memory bounded without exact trimming overhead.

---

## 3. Task Checkpoint Protocol

### Write

Called by any worker at meaningful progress milestones (e.g., after each sub-task, each chunk processed):

```python
await _swarm_checkpoint_write(task_id, worker_id, progress=40, total=100, state={"last_chunk": 12})
```

Stored in Redis hash `swarm:checkpoint:{task_id}`:
```
status      = "in_progress" | "complete" | "failed"
worker_id   = <uuid>
progress    = "40"
total       = "100"
state       = <json string>
updated_at  = <iso timestamp>
```

### Read

```python
cp = await _swarm_checkpoint_read(task_id)
# Returns dict or None
```

### Marking Complete

Worker writes `status=complete` via `POST /swarm/task/checkpoint` with `progress == total`.

---

## 4. Worker Boot Recovery Sequence

On lifespan startup, after Redis connection established:

```
1. Create consumer groups (XGROUP CREATE, catch BUSYGROUP)
2. Call _swarm_recover_pending_checkpoints()
3. Scan swarm:checkpoint:* keys in Redis
4. For each with status == "in_progress":
   a. Re-enqueue task_id to swarm:queue:high LPUSH
   b. Emit a task.recovered event to swarm:events
5. Log recovered count
```

This ensures interrupted tasks (power loss, OOM kill, SIGKILL) are re-tried on next worker cycle. The in-progress checkpoint acts as a crash beacon.

**Idempotency note**: Re-enqueued tasks may run twice if the first run had already written a result. Workers should check for existing results before overwriting.

---

## 5. Per-Worker Intelligence Accumulation

### Storage

Worker runtime stats are accumulated in an in-process dict `swarm_intelligence_stats`:
```python
swarm_intelligence_stats: Dict[str, Any] = {}
```

And persisted to Redis hash `swarm:intelligence:workers` for multi-process / restart durability.

### Fields Per Worker

```
total_tasks   = int
total_tokens  = int
total_duration = float (seconds)
success_count = int
fail_count    = int
last_seen     = iso timestamp
worker_type   = str
```

### Recorded After Each Task

In `_swarm_worker_loop`, after success:
```python
await _swarm_intelligence_record(result)
```

And after failure, using an explicit `_fail_result` dict:
```python
_fail_result = {
    "task_id": task_id,
    "worker_id": worker_id,
    "worker_type": worker_type,
    "status": "failed",
    "duration": elapsed,
    "token_count": 0,
}
await _swarm_intelligence_record(_fail_result)
```

---

## 6. Graph Snapshot Endpoint

`GET /swarm/graph/snapshot`

Returns live topology useful for cockpit visualization:

```json
{
  "nodes": [
    {"id": "queue", "type": "queue", "label": "Task Queue", "status": "active", "count": 4},
    {"id": "abc12345", "type": "worker", "label": "general\nabc12345", "status": "running", "runtime": "142s", "worker_type": "general"}
  ],
  "edges": [{"source": "queue", "target": "abc12345"}],
  "workers": [...],
  "queue_depth": 4,
  "recent_event_types": ["task.completed", "task.dispatched"],
  "snapshot_at": "2025-01-01T00:00:00"
}
```

Edges connect `queue → worker` for each active worker to show live claim topology.

---

## 7. Intelligence Summary Endpoint

`GET /swarm/intelligence/summary`

Aggregates across all workers:

```json
{
  "total_tasks": 120,
  "succeeded": 115,
  "failed": 5,
  "success_rate": 95.8,
  "avg_duration_seconds": 8.4,
  "best_worker_id": "abc12345",
  "slowest_task_id": null,
  "recommended_strategy": "maintain"
}
```

Strategy logic:
- `scale_up` → queue depth > 10 AND worker count < 8
- `scale_down` → all workers idle AND queue depth == 0
- `maintain` → otherwise

---

## 8. IDE Independence Rule

This is an infrastructure principle, not a code change:

> The cognitive state of the system (memory, task queue, checkpoints) must not depend on any IDE, editor, or Copilot session being alive.

All durable state lives in:
- Redis (events, streams, checkpoints, intelligence stats, timeline, knowledge)
- Qdrant (vector memory)

Nothing important lives in: VSCode state, editor tabs, IDE workspace memory, or browser session.

The cockpit UI reads from Redis/FastAPI only. Closing the browser loses no data.

---

## 9. Second Brain Ingestion Pipeline

Planned (not yet implemented). Target flow:

```
swarm:results:stream
    → XREADGROUP by "second-brain-consumer"
    → Filter for status=success AND memory_key != null
    → Upsert into Qdrant collection "second_brain"
    → XACK after successful vector write
    → Emit "memory.ingested" event to swarm:events:stream
```

This is a separate async background task, not a worker. Runs as `_second_brain_ingest_loop` in lifespan startup.

---

## 10. Environment Flags

| Variable | Default | Effect |
|---|---|---|
| `USE_REDIS_STREAMS` | `false` | Enables XADD dual-write in emit_event + store_result |
| `ENFORCE_OPERATOR_TOKEN` | `false` | Requires bearer token on control-plane endpoints |
| `SNAC_OPERATOR_TOKEN` | — | Secret token value (set in VPS .env, never committed) |

---

## Status

- [x] Streams dual-write: `_swarm_emit_event`, `_swarm_store_result`
- [x] Consumer group creation on startup
- [x] Task checkpoint write/read helpers
- [x] Boot crash recovery: `_swarm_recover_pending_checkpoints`
- [x] Intelligence recording in worker loop (success + failure paths)
- [x] `/swarm/graph/snapshot` endpoint
- [x] `/swarm/intelligence/summary` endpoint
- [x] `/swarm/task/checkpoint` POST + GET endpoints
- [x] UI: `SwarmGraphPanel` component
- [x] UI: `SwarmIntelligencePanel` component
- [x] CSS for graph + intelligence panels
- [x] **VPS deployed** — `187.77.3.56`, backend rebuilt, health + swarm/status verified (2026-03-12)
- [x] `USE_REDIS_STREAMS=true`, `ENFORCE_OPERATOR_TOKEN=true`, `SNAC_OPERATOR_TOKEN` set in VPS .env
- [ ] Second brain XREADGROUP ingest loop
- [ ] IDE independence enforcement (no ephemeral state)
- [ ] Qdrant upsert from result stream
