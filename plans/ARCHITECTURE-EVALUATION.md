# SNAC v2 Architecture Evaluation

**Evaluator:** Architect Review  
**Date:** 2026-03-11  
**Mode:** Architect Planning Mode

---

## High-Level Assessment

### The Good
- Phased approach is sound — foundation (DBs) → agent → UI → hardening
- Single VPS constraint avoids multi-server sprawl
- LangGraph + LlamaIndex + AutoGen is a solid, free stack choice
- Zero-backend-change UI components — the "observable-only" philosophy is architecturally pure
- Budget guardrails at $4.50/month — critical for $5 VPS economics
- Health checks on all services — prevents cascading startup failures

### The Concerns
- Orchestrator architecture is unclear — Docs 2-3 show AutoGen + LangGraph integration, but actual implementation path is fuzzy
- n8n is still missing — planned since Doc 2, not deployed
- No nginx — planned for SSL, not deployed (ports 8000/3000 exposed directly)
- Agent state persistence — Doc 10 celebrates "ephemeral memory" but production needs conversation history
- Tool sandboxing in Doc 13 is conceptual — no actual code provided
- Cost model in Doc 11 is unrealistic — $0.00045 per RAG assumes GPT-3.5; GPT-4 is $0.03/1k tokens

---

## Critical Gaps

| Gap | Risk Level | Impact |
|-----|------------|--------|
| No n8n | 🔴 High | No automation — manual triggering only |
| No nginx/SSL | 🔴 High | Exposed ports, no HTTPS, security risk |
| Ephemeral-only memory | 🟡 Medium | Agent forgets everything after restart |
| No actual tool allowlist | 🟡 Medium | Doc 13 mentions sandboxing but no implementation |
| Cost model uses wrong pricing | 🟡 Medium | Budget will burn faster than expected |

---

## What's Actually Deployed vs. Planned

| Component | Planned (Doc 3) | Actually Running |
|-----------|-----------------|-----------------|
| Backend (FastAPI) | ✅ | ✅ snac_backend:8000 |
| Frontend (Next.js) | ✅ | ✅ snac_frontend:3000 |
| PostgreSQL | ✅ | ✅ snac_db:5432 |
| Redis | ✅ | ✅ snac_redis:6379 |
| Qdrant | ✅ | ✅ snac_qdrant:6333-34 |
| Nginx | ✅ | ❌ Missing |
| n8n | ✅ | ❌ Missing |

**Status: 5/7 services deployed. Missing: nginx, n8n.**

---

## Specific Architectural Issues

1. **Doc 3's docker-compose.yml is monolithic** — all services in one file works for now but will become unwieldy. Consider splitting to `docker-compose.infra.yml` and `docker-compose.app.yml`.

2. **AutoGen + LangGraph integration in Doc 3 is naive** — the `planner.py` example calls `initiate_chat` inside a LangGraph node, which will block. Real implementation needs async.

3. **Doc 10's "ephemeral memory" is a feature, not a bug** — but persistent memory is needed. Postgres is there but not wired for conversation history.

4. **No rollback strategy** — Doc 2 mentions `docker compose up -d --scale` but this isn't implemented.

---

## Recommendations (Priority Order)

1. **Add nginx** — for SSL and rate limiting (Doc 13, Layer 1)
2. **Add n8n** — for automation (Doc 6)
3. **Wire Postgres for conversation history** — the DB is there but not storing chat
4. **Fix cost model** — use actual OpenAI pricing
5. **Add tool allowlist code** — Doc 13 promises it but doesn't deliver

---

## Summary

- **Architecture Design:** 70% complete
- **Deployed:** 50% complete
- **Foundation:** Solid
- **Observability story:** Strong (WebSocket + TTS)
- **Missing pieces:** nginx, n8n, persistent conversation storage

**Next concrete step:** Deploy nginx and wire it as reverse proxy with rate limiting. That's Layer 1 of production hardening.
