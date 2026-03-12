# Planning Document 14: Zero-to-Observable Launch Path

## Overview

Zero-to-observable, battle-tested launch path for SNAC v2 - designed for clean slate.

**Total time to first observable agent cycle**: 25 minutes

---

## PHASE 0: PREREQUISITES (5 MINUTES)

### Steps
1. Provision $5 VPS (Ubuntu 22.04 LTS)
2. SSH in & update system
3. Create project directory & .env

```bash
mkdir -p /opt/agent-system && cd /opt/agent-system
cat > .env <<EOF
OPENAI_API_KEY=sk-...
POSTGRES_PASSWORD=agent_secure_password_$(openssl rand -hex 8)
EOF
chmod 600 .env
```

---

## PHASE I: FOUNDATION (8 MINUTES)

Goal: Running DBs + Nginx proxy. Must see healthy logs before touching agent code.

### Steps
1. Start ONLY infrastructure (postgres, redis, qdrant, nginx)
2. Wait for health (docker compose ps)

### Verification
- All services show `healthy` under STATE
- If not healthy: `docker compose logs [failing-service]`

---

## PHASE II: AGENT BACKBONE (7 MINUTES)

Goal: Agent responds to a task → cockpit updates.

### Steps
1. Add agent services (backend, cockpit, n8n)
2. Build & start: `docker compose up -d --build`
3. Wait for backend ready
4. Send first task & observe cockpit

### Commands
```bash
# Ingest test doc
curl -s -X POST http://localhost:8000/ingest -H "Content-Type: text/plain" --data-binary "The capital of Japan is Tokyo. 2+2=4."

# Send task
curl -s -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task":"QUERY: What is the capital of Japan? Then CALC: 25 * 4"}'
```

### Verification (Cockpit at http://localhost:3000)
- **Memory Timeline**: Shows PLAN → STEP → TOOL → RESULT
- **Node Visualizer**: Planner → Worker 1 (active) → Worker 2 (pending) → END
- **Token Cost Monitor**: Shows non-zero cost
- **Live Logs**: WebSocket updates

---

## PHASE III: HARDENING (5 MINUTES)

Goal: Add budget limits, timeouts, and throttling.

### Steps
1. Set OpenAI budget hard limit ($4.50)
2. Add NGINX rate limiting
3. Add request timeouts

### Verification
- Rate limit: 25 requests → 429 for requests 11+
- Timeout: `curl -m 1` → 504 Gateway Timeout

---

## PHASE IV: FIRST USEFUL TASK (5 MINUTES)

Goal: Run task that uses RAG + math + tool → verify all panels update.

### Commands
```bash
# Ingest knowledge
curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: text/plain" \
  --data-binary "The capital of France is Paris. The speed of light is 299792458 m/s."

# Send compound task
curl -s -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task":"QUERY: What is the capital of France? Then CALC: 299792458 / 1000000"}'
```

---

## VALIDATION CHECKLIST

| Checkpoint | Success Signal |
|------------|---------------|
| Infrastructure healthy | All services `healthy` |
| Backend reachable | `{"status":"ok"}` |
| First task triggers cockpit | All 3 panels update in <5s |
| Rate limiting works | Requests 11+ return `429` |
| Timeout works | `504 Gateway Timeout` |
| Budget guardrail active | Alerts at $4.00; blocks at $4.50 |
| No state drift | Cockpit rebuilds identically after restart |

---

## Final Validation Command

```bash
curl -s -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task":"QUERY: What is 2+2? Then CALC: result * 3"}'
```

This proves the agent uses its own prior output (working memory).
