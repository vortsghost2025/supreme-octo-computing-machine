# Crash Assessment — Memory Safety Analysis
*Saved: 2026-03-15 — post-crash review after VPS rebuild*

---

## What Actually Happened (Root Cause Chain)

```
48-layer memory bank
   ↓ swarm agents writing constantly
   ↓ memory sync across agents
   ↓ vector embeddings per thought
   ↓ log + cache explosion
   ↓ disk thrash
   ↓ WSL2 triple-layer filesystem writes simultaneously
   ↓ Windows filesystem corruption
```

WSL2 made it far worse — three filesystems writing at once:

```
Windows FS  ↕  WSL ext4 virtual disk  ↕  Docker overlayfs
```

One runaway memory loop at swarm scale = disk full + filesystem corruption.

---

## Specific Trigger: Unbounded Write Storm

```
1 agent thought → 10 writes → 100 writes → 1000 writes
```

Agent thought → memory write → vector embed → timeline event  
→ cross-agent sync → more memory writes → repeat

At `@swarm` scale (5 agents simultaneously) this multiplied by 5× per cycle.

---

## Fix 1 — Memory Governor 🔴 High Priority

Add to `.env`:

```
MAX_WRITES_PER_MINUTE=200
MAX_VECTOR_INSERTS=50
MAX_MEMORY_SIZE_MB=500
```

Behaviour when exceeded: memory writes pause, agents continue thinking,
only final results are stored.  Already wired into `.env.example`.

---

## Fix 2 — Memory Compression Layer 🟡 Medium Priority

Instead of storing every intermediate thought, compress before storage:

```
10 agent thoughts → compressor → cluster → 1 summarized memory
```

Pipeline:

```
Agents → Event Bus (Redis) → Memory Buffer → Compression Engine → Vector DB / Postgres
```

This single buffer layer prevents runaway memory storms.

---

## Fix 3 — Safe Rebuild Mode 🔴 High Priority

Before reconnecting everything after a crash, enable safe mode:

```
SNAC_SAFE_MODE=true
```

When enabled:
- Disables: memory sync, vector embedding, swarm spawn
- Only allows: 1 agent, 1 memory store, 1 task
- Scale back slowly once stable

Already wired into `.env.example`.

---

## Fix 4 — The Free Coding Agent Was an Orphan Container 🔴 Fixed

`snac_free_coding_agent` was deployed manually on the VPS at port 3001 but
was never added to `docker-compose.yml`.  This caused two problems:

1. Docker treated it as an orphan — `--remove-orphans` killed it silently.
2. When it was running, Kilo's MCP client got responses from two agent
   endpoints simultaneously → Kilo crashed.

**Status: Fixed** — `snac_free_agent` is now a proper service in
`docker-compose.yml` with container name `snac_free_agent`.

---

## Fix 5 — @swarm Multiplied Everything

The `@swarm` mode (5 parallel agents) is safe once the memory governor is
in place.  Before the governor, every `@swarm` invocation created 5× the
write storm.

**Rule until governor is active:** use single modes (`@coder`, `@debugger`)
instead of `@swarm`.

---

## Priority Table

| Priority | Task | Effort | Status |
|----------|------|--------|--------|
| 🔴 Now | `SNAC_SAFE_MODE=true` in .env | Trivial | ✅ In .env.example |
| 🔴 Now | Memory governor env vars | Small | ✅ In .env.example |
| 🔴 Now | Free agent added to compose | Small | ✅ Done |
| 🟡 Soon | Memory buffer between agents and storage | Medium | ⬜ Planned |
| 🟡 Soon | Memory compression engine | Medium | ⬜ Planned |
| 🟢 Later | Full swarm memory safety architecture | Large | ⬜ Planned |

---

## Recovery Checklist After Any Crash

1. Set `SNAC_SAFE_MODE=true` in `.env` on the VPS
2. Redeploy: `docker compose up -d --build --remove-orphans`
3. Verify VPS disk: `df -h` — must have at least 5 GB free before swarm
4. Test with a single agent (`@coder`) before enabling `@swarm`
5. Once stable for 24 hours, set `SNAC_SAFE_MODE=false`

---

## What Was Lost vs What Remains

| Category | Lost | Survived |
|----------|------|----------|
| Runtime state | Agent memory, active tasks | — |
| Code | Some in-progress edits | Core backend, UI, infra |
| Architecture | — | All of it (in `plans/`) |
| Infrastructure | — | Docker Compose, nginx, VPS config |
| Documentation | — | All of it |

The hardest parts (architecture, deployment model, infrastructure topology)
all survived.  The lost pieces are the fastest to rebuild.

---

## Honest Reality Check

- **"0ms latency"** is almost certainly a timer-resolution artifact or cached response.
  Still impressive, but don't advertise literal 0ms.
- The architecture is solid. What was lost was runtime state, not design.
