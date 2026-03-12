# AGENT-START-HERE.md
# READ THIS BEFORE DOING ANYTHING ELSE IN THIS REPO

---

## CRITICAL FACTS — DO NOT ASSUME OTHERWISE

### 1. THE BACKEND AND FRONTEND ARE ALREADY DEPLOYED AND RUNNING ON A VPS
- This is NOT an empty project.
- This is NOT a greenfield scaffold.
- Do NOT suggest "let's start by building the backend."
- The services are live on a Hostinger VPS.
- Production runtime truth is the Docker stack on the Hostinger VPS, not this Windows machine.
- Local Docker is only for development, reproducing issues, or preparing changes that will be redeployed to the VPS.
- Do NOT treat local rebuilds as the default recovery path when SSH or VPS edits fail.

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
- Active compose working dir on VPS: /opt/snac-v2/backend
- Compose file on VPS: /opt/snac-v2/backend/docker-compose.yml
- Note: /opt/agent-system is stale in older docs and should not be assumed.
- Backend API: http://187.77.3.56:8000
- Frontend: http://187.77.3.56:3000

### 4. LOCAL REPO PATH (THIS MACHINE)
- Working code: S:\snac-v2\snac-v2
- Git root: S:\snac-v2\snac-v2
- Do NOT treat S:\ as project root.
- Make code changes locally, commit locally, and redeploy to the VPS when runtime changes are needed.

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
8. Treat the Hostinger VPS Docker deployment as the source of runtime truth.
9. Only use local Docker to test or package changes before pushing and redeploying to the VPS.
10. If SSH-based edits fail, troubleshoot the VPS containers and redeploy from this repo instead of rebuilding the system from scratch locally.

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
   - `ssh root@187.77.3.56 "cd /opt/snac-v2/backend && docker compose ps"`
4. Verify API health from VPS host:
   - `ssh root@187.77.3.56 "curl -fsS http://localhost:8000/health"`
5. Verify recent container failures before claiming system is down:
   - `ssh root@187.77.3.56 "docker ps -a --format '{{.Names}}|{{.Status}}'"`

If these checks are not run, do NOT suggest rebuilding stack components.

If SSH changes are failing, the fallback is:

1. Diagnose the live VPS containers first.
2. Make required code or config changes in S:\snac-v2\snac-v2.
3. Commit and push from this standalone repo.
4. Redeploy the Docker stack on the VPS from the updated repo.

It is not acceptable to treat local-only rebuilds as production recovery.

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
