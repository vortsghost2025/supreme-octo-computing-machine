# AGENT-START-HERE.md
# READ THIS BEFORE DOING ANYTHING ELSE IN THIS REPO

---

## CRITICAL FACTS — DO NOT ASSUME OTHERWISE

### 1. THE BACKEND AND FRONTEND ARE ALREADY DEPLOYED AND RUNNING ON A VPS
- This is NOT an empty project.
- This is NOT a greenfield scaffold.
- Do NOT suggest "let's start by building the backend."
- The services are live on a Hostinger VPS.

### 2. VPS DEPLOYMENT STATE (LIVE AS OF 2026-03-11)
| Service        | Container         | Port  | Status   |
|----------------|-------------------|-------|----------|
| FastAPI backend| snac_backend      | 8000  | RUNNING  |
| React frontend | snac_frontend     | 3000  | RUNNING  |
| PostgreSQL 15  | snac_db           | 5432  | RUNNING  |
| Redis 7        | snac_redis        | 6379  | RUNNING  |
| Qdrant         | snac_qdrant       | 6333  | RUNNING  |
| Nginx          | —                 | 80    | MISSING  |
| n8n            | —                 | 5678  | MISSING  |

### 3. VPS LOCATION
- IP: 187.77.3.56
- SSH: root@187.77.3.56
- Project path on VPS: /opt/agent-system
- Backend API: http://187.77.3.56:8000
- Frontend: http://187.77.3.56:3000

### 4. LOCAL REPO PATH (THIS MACHINE)
- Working code: S:\snac-v2\snac-v2
- Git boundary problem: git root is currently S:\ (too broad)
- Do NOT treat S:\ as project root — only work inside S:\snac-v2\snac-v2

---

## WHAT IS ACTUALLY MISSING (THE REAL WORK)

These two services are planned but NOT yet deployed:

1. **Nginx** — needed for SSL, rate limiting, unified port 80/443
   - Config exists at: `nginx/nginx.conf` (has a nesting bug, see below)
   - Fix nginx.conf nested location blocks before deploying

2. **n8n** — automation/workflow engine
   - Planned since Doc 2
   - Not yet in docker-compose

Other gaps:
- `backend/main.py` currently contains only placeholder text — needs real FastAPI implementation
- Postgres is running but NOT wired for conversation history storage
- No tool allowlist/sandboxing implemented yet (planned in plans/13-production-hardening-guide.md)

---

## NGINX CONFIG BUG (DO NOT DEPLOY AS-IS)
File: `nginx/nginx.conf`
Problem: `location /` is nested inside `location /` — invalid nginx syntax.
Fix: Make all location blocks siblings at the same level inside the `server {}` block.

---

## ARCHITECTURE STACK
- Backend: FastAPI (Python)
- Frontend: React (Vite)
- Agent orchestration: LangGraph + AutoGen (planned)
- Vector DB: Qdrant
- Relational DB: PostgreSQL 15
- Cache: Redis 7
- Proxy: Nginx (not yet deployed)
- Automation: n8n (not yet deployed)
- Infra: Docker Compose on single $5 VPS

---

## PLANS FOLDER
All architecture decisions are documented in `plans/`:
- 01–03: Initial architecture and foundation
- 04–05: Critical fixes and SSL
- 06–07: Cockpit UI panel
- 08–10: Memory and timeline features
- 11–12: Token cost monitoring
- 13: Production hardening
- 14: Launch path (zero-to-observable, 25 min sequence)
- 15: Hostinger VPS deployment specifics
- ARCHITECTURE-EVALUATION.md: Honest gap analysis — read this first

---

## WORKING RULES FOR ALL AGENTS
1. Always SSH to VPS to verify live state before assuming anything is missing.
2. Never overwrite existing docker-compose without checking running containers first.
3. Never commit .env files — root .gitignore is now in place.
4. Work from S:\snac-v2\snac-v2, not from S:\ root.
5. The frontend folder in this repo is `ui/`, not `frontend/`.
6. The backend folder is `backend/`.
7. Check plans/ARCHITECTURE-EVALUATION.md before proposing new architecture.

---

## SESSION CONTINUITY GUARD (ANTI-REBUILD)

Before proposing any rebuild, every agent MUST run this sequence:

1. Verify scheduler/key-rotation state locally:
   - `Get-ScheduledTask -TaskName "SNAC-v2-Rotate-API-Keys" | Select-Object TaskName,State,TaskPath`
2. Verify local rotation files exist:
   - `.env`
   - `.env.rotation`
   - `scripts/rotate-api-keys.ps1`
3. Verify VPS live state over SSH:
   - `ssh root@187.77.3.56 "cd /opt/agent-system && docker compose ps"`
4. Verify API health from VPS host:
   - `ssh root@187.77.3.56 "curl -fsS http://localhost:8000/health"`
5. Verify recent container failures before claiming system is down:
   - `ssh root@187.77.3.56 "docker ps -a --format '{{.Names}}|{{.Status}}'"`

If these checks are not run, do NOT suggest rebuilding stack components.

---

## KEY ROTATION STATE (LOCAL MACHINE)

Rotation implemented on 2026-03-12.

- Scheduled task name: `SNAC-v2-Rotate-API-Keys`
- Rotation script: `scripts/rotate-api-keys.ps1`
- Scheduler setup script: `scripts/setup-rotation-scheduler.ps1`
- Rotation audit log: `logs/rotation-audit.log`
- Secret files (must stay local):
  - `.env`
  - `.env.rotation`

Git ignore protection exists in repo-local `.gitignore`.

Agents must never print or commit key values.
