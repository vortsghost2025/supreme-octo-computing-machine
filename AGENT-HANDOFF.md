# Agent Handoff

This document is for the next agent or reviewer working on this machine and repo.

## Current Goal

Stabilize and organize the SNAC project boundaries without damaging active work.

## Human Context

- User builds very quickly and has a large amount of recent machine state.
- User has low vision and relies heavily on text-to-speech.
- Prefer short, explicit, low-chaos steps.
- Do not propose broad cleanup or destructive commands without a rollback path.

## Important Boundaries

- Intended SNAC envelope: `S:\snac-v2`
- Current SNAC working code folder: `S:\snac-v2\snac-v2`
- Current SNAC git root: `S:\snac-v2\snac-v2`
- User/tool state mostly lives on `C:\Users\seand`
- VPS runtime truth lives on the Hostinger VPS in Docker at `/opt/snac-v2/backend`
- Local work is for code changes and validation before pushing/redeploying to the VPS

## Verified Findings

1. `S:\snac-v2\snac-v2` is now a standalone git repository.
2. The current MCP workspace and git root are both `S:\snac-v2\snac-v2`.
3. Parent-repo contamination was the cause of earlier false-positive git reviews.
4. Kilo internal MCP filesystem scope was narrowed to `S:\snac-v2\snac-v2` for isolation.
5. Hostinger MCP was disabled in Kilo internal settings to stop restart/disconnect instability.
6. Production is the Docker deployment on the Hostinger VPS, not a local Windows Docker stack.

## Files Added During Stabilization

- `S:\.gitignore`
- `S:\snac-v2\snac-v2\SYSTEM-MAP.md`
- `S:\snac-v2\snac-v2\KILO-ISOLATION.md`
- `S:\snac-v2\snac-v2\MCP-MODES.md`
- `S:\snac-v2\snac-v2\audit-machine-layout.ps1`
- `S:\snac-v2\snac-v2\set-kilo-snac-mode.ps1`
- `S:\snac-v2\snac-v2\set-kilo-fullhome-mode.ps1`
- `S:\snac-v2\snac-v2\set-mcp-local.ps1`
- `S:\snac-v2\snac-v2\set-mcp-hostinger.ps1`

## Safe Conclusions

1. Do not treat `S:\` as the logical project root.
2. Do not create placeholder files to satisfy stale extension references.
3. Do not run blanket restore or checkout commands on browser/runtime paths.
4. Do not move folders on `S:` or `C:` until duplicates and ownership are mapped.
5. Review and implementation should target the SNAC repo boundary, not the whole drive.
6. When production issues happen, verify and repair the VPS Docker deployment first.
7. Use local Docker only to test changes that will then be pushed and redeployed to the VPS.

## Commands That Should NOT Be Run Blindly

- `git restore ...` on broad paths like `kilo/`, `chrome-win/`, or `workspace/`
- `git checkout -- ...` on broad paths
- deleting `S:\.git`
- moving `S:\snac-v2` or `S:\snac-v2\snac-v2` in File Explorer without a plan
- full recursive scans of all 500GB unless needed for a specific question

## Current Review Status

- Repository isolation: complete
- Browser artifact contamination: addressed safely
- Parent-repo git noise no longer applies to this standalone SNAC repo
- Remaining work should focus on product/runtime changes, not repo-boundary cleanup

## Recommended Next Steps

1. Run the read-only audit script:
   `./audit-machine-layout.ps1`
2. Use the output to identify canonical project locations and obvious duplicates.
3. Keep Kilo in SNAC-only mode while working in this repo.
4. Prefer VPS-first diagnostics for production issues.
5. Make fixes locally only when they need to be committed and redeployed to the VPS Docker stack.

## Reset-Safety Rules (Do Not Skip)

These rules exist because agent resets have repeatedly caused duplicate rebuild work.

1. Never assume stack is missing after a reset.
2. Run a live-state preflight before any architecture proposal:
   - `Get-ScheduledTask -TaskName "SNAC-v2-Rotate-API-Keys" | Select-Object TaskName,State,TaskPath`
   - `ssh root@187.77.3.56 "cd /opt/snac-v2/backend && docker compose ps"`
   - `ssh root@187.77.3.56 "curl -fsS http://localhost:8000/health"`
3. If these checks pass, do not scaffold or rebuild backend/frontend.
4. Prefer targeted repair (container restart, env fix, nginx fix, DB connectivity) over rebuild.
5. If direct SSH editing is failing, make the change in this repo, push it, and redeploy the VPS Docker stack.

## Key Rotation Implementation Snapshot

Implemented locally on 2026-03-12.

- `.env` and `.env.rotation` are present in repo root.
- Rotation script: `scripts/rotate-api-keys.ps1`
- Task setup script: `scripts/setup-rotation-scheduler.ps1`
- Scheduled task: `SNAC-v2-Rotate-API-Keys` (daily 2:00 AM)
- Audit log path: `logs/rotation-audit.log`

Do not expose keys in chat, logs, or commits.

## If Another Agent Takes Over

Start here:

1. Read `SYSTEM-MAP.md`
2. Read `KILO-ISOLATION.md`
3. Read `MCP-MODES.md`
4. Read this file
5. Ask before any destructive cleanup

## Why This Exists

There is too much machine state to rediscover repeatedly. This file preserves the stabilization work already done so future agents do not re-contaminate the repo boundary or repeat unsafe advice.

## 2026-03-11 / 2026-03-12 Delta (Latest)

### Completed and Deployed

1. Cockpit accessibility and layout redesign (Option C focus mode) is live.
2. Thought ingestion MVP is live:
   - `POST /ingest-thought`
   - UI Quick Thought panel in sidebar
   - Timeline event `thought_ingest`
3. Swarm Phase 1 foundation is live:
   - `POST /swarm/task`
   - `GET /swarm/status`
   - `POST /swarm/scaler/tick`
   - `GET /swarm/events/recent`
   - `POST /swarm/config`
   - Cockpit Swarm Queue sidebar input + Swarm Monitor panel
   - Timeline events `swarm_task_created`, `swarm_scaler_decision`
4. Persistent shared knowledge Phase A is live:
   - `POST /memory/learn`
   - `GET /memory/feed`
   - Cockpit Add Learning sidebar form + Shared Knowledge panel
   - Timeline event `memory_learn`

### Verified Live API Checks

- `POST /api/ingest-thought` returns success payload with category, confidence, and links.
- Swarm queue/status/tick/events endpoints return valid data through nginx TLS endpoint.
- `POST /api/memory/learn` and `GET /api/memory/feed` both verified with live sample item.

### Planning Docs Added

- `plans/18-cockpit-visual-options.md`
- `plans/19-ai-operating-system-cognitive-architecture.md`
- `plans/20-self-expanding-agent-swarm.md`
- `plans/21-persistent-memory-bank-spec.md`

### Important Notes For Next Agent

1. Do not import external project code directly; only port patterns and concepts.
2. Continue Phase 2 swarm work by adding real worker lifecycle and queue consumers.
3. Next memory step is injection preview/apply policies from `plans/21-persistent-memory-bank-spec.md`.
4. Keep endpoint compatibility under nginx `/api` prefix.
5. Keep the deployment model explicit: production runs on the Hostinger VPS in Docker; local work exists to change code and redeploy, not to replace production with a local rebuild.