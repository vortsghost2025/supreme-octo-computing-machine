# Unified Control Plane Roadmap (Hostinger + Next.js)

Last updated: 2026-03-12
Owner: Sean
Status: Active working plan

## 1) Strategic Direction

Use one unified Next.js app as the primary control plane, hosted on Hostinger VPS.
Keep Oracle as optional compute for heavy/background workloads, not as the first-hop runtime for every request.
Treat split frontend/backend experiments (especially fragile Svelte split stacks) as source material, not primary production architecture.

## 2) Why This Direction

- Lower integration overhead than split frontend/backend stacks.
- Faster iteration and recovery when things drift.
- Single deploy target and clearer failure domain.
- Fits current execution style: high velocity, low tolerance for glue code breakage.

## 2.5) Core Working Truth

Everything tends to combine because it is the same puzzle viewed through different domains.
Repeated patterns across projects are not noise. They are evidence of recurring primitives that should be promoted into shared architecture.

Interpret repetition as signal for:
- shared orchestration patterns
- shared memory patterns
- shared control-plane patterns
- shared safety/governance patterns
- shared capture and condensation patterns

Do not force artificial separation when the same structural motif keeps reappearing. Instead, extract the motif and make it canonical.

## 3) Architecture Decisions

### A. Control Plane
- Framework: Next.js (App Router)
- Host: Hostinger VPS (primary)
- Pattern: UI + API routes/server actions in one repo

### B. Agent Runtime Boundaries
- Cockpit is UI/control surface only.
- Orchestration lives in backend functions/routes.
- External agents (Claw, others) must be behind adapters.
- Never bind cockpit endpoint and external agent endpoint to the same identity/session namespace.

### C. Session and Endpoint Safety
- Use unique session prefixes by domain:
  - snac:<session>
  - claw:<session>
  - cloud:<session>
- Prohibit dual ownership of one endpoint.
- No proxy loops (cockpit -> claw -> cockpit).

### D. Compute Strategy
- Hostinger: primary app, orchestration, dashboards, standard workloads.
- Oracle: optional worker pool for heavy jobs only.
- Docker local: fastest dev/test bootstrap.

## 4) Immediate Execution Plan (90-minute bootstrap)

1. Pick one project as the canonical Next.js control plane base.
2. Stand up baseline on Hostinger (single domain, HTTPS, envs).
3. Port highest-value API surface into Next.js route handlers.
4. Add one adapter route for one external agent (no direct endpoint sharing).
5. Validate health, auth/session, and one end-to-end task path.
6. Freeze architecture and replicate pattern to remaining apps.

## 5) Migration Plan (Split Stack -> Unified Next.js)

### Phase 1: Stabilize Core (Day 1)
- Create health endpoints and status page.
- Move critical API calls into unified routes.
- Add structured logs and request IDs.

### Phase 2: Agent Integration (Day 2)
- Implement adapter interface for external agents.
- Add timeout, retry, and circuit-breaker behavior.
- Enforce session namespace isolation.

### Phase 3: Memory and Swarm (Day 3)
- Keep memory as a subsystem, not transport.
- Add queue-backed swarm jobs (not just simulated scaler events).
- Expose clear observability panel in cockpit.

### Phase 4: Hardening (Day 4)
- Guardrails for rate limits, budgets, and retries.
- Secrets cleanup and env audit.
- Backup/restore and rollback script.

## 6) Known Failure Patterns To Avoid

- "Double endpoint" ownership (cloud agent + cockpit pretending to be same endpoint).
- Session collision across local/cloud/CLI channels.
- Transport mismatch on one URL (websocket vs plain HTTP expectations).
- Turning cockpit into runtime instead of a control surface.

## 7) Recovery Checklist (If Something Breaks)

1. Confirm endpoint ownership map (who owns each URL).
2. Confirm session namespace isolation.
3. Confirm transport type per endpoint.
4. Disable cross-calling/proxy loops.
5. Route all UI calls through one backend adapter layer.
6. Re-run smoke test: health -> auth -> task -> timeline -> cost.

## 8) Weather Project Track (Discovered)

Strong candidate weather stack:
- C:\workspace\global-weather-federation

Signals found:
- NOAA/NASA/ECMWF integration in server code.
- Harvest, predict, analyze endpoints.
- Docker + cloud deployment scripts (Hostinger/Oracle/AWS/Alibaba).

Recommended path:
- Revive with Docker locally first.
- Promote to Hostinger for always-on control plane.
- Offload heavy compute to Oracle only when needed.

## 9) "Forest Not Tree" Portfolio Method

Use this for all projects to stop repo sprawl from slowing execution:

- Bucket every project into one of:
  - SHIP NOW
  - CORE PLATFORM
  - RESEARCH
- Keep only top 2 active at once.
- Archive everything else with a one-line purpose and last-known-good entrypoint.

## 9.5) Compression-Horizon Planning

Do not rely on long fixed roadmaps if execution regularly compresses months of work into days.

Use this planning stack instead:
- North Star: what the whole system becomes
- This Week: the current frontier
- Today: concrete packets that become real
- Now: the single active edge
- Overflow: everything captured but not scheduled

The goal is not time-horizon planning. The goal is convergence under fast-moving context.

## 9.6) Cross-Project Primitive Ledger

When the same ideas recur across game, weather, medical, swarm, cockpit, IDE, and memory systems, capture them as primitives instead of duplicating them as project-specific inventions.

Current likely primitives:
- inbox and capture
- orchestration and delegation
- memory layers and retention
- consensus and veto
- cockpit visibility and control
- role-based agent execution
- unified control plane
- bounded autonomy with safety envelopes

## 10) Copy/Paste Handoff Prompt (For Claude Code or Other Agent)

Use this block as a bootstrap handoff:

"""
You are inheriting a unified-control-plane migration.
Primary goal: run one Next.js control plane on Hostinger VPS.
Do not build split frontend/backend unless explicitly required.
Do not merge cockpit endpoint identity with external agent endpoints.
Use adapter routes for external agents and isolate sessions with prefixes.
Start with one end-to-end path: health, task run, timeline, token/cost metrics.
Then add queue-backed swarm execution and observability.
If conflicts arise, prefer simpler deployability over architectural purity.
"""

## 11) Working Notes (User edits)

- [ ] Next idea:
- [ ] Next blocker:
- [ ] Repo/path to apply this on:
- [ ] Decision made today:
- [ ] What to defer:

## 12) Definition of Done (for v1)

- One unified Next.js control plane deployed on Hostinger.
- External agent integration via adapters only.
- No endpoint/session collisions.
- One reliable orchestration workflow production-stable.
- Recovery runbook verified.
