# Planning Document 13: Production Hardening Guide

## Overview

Zero-backend-change, SNAC v2-compliant operational playbook for production resilience.

## Layers of Hardening

### Layer 1: External Throttling (NGINX)
Prevents abuse/replay attacks at network layer - never touches agent state.

**Add to nginx.conf:**
- Rate limiting: 10 req/sec per IP for API
- Rate limiting: 5 WS conn/sec per IP
- Block common attack patterns

### Layer 2: OpenAI Budget Enforcement
Uses OpenAI's native dashboard - zero code change.

**Settings:**
- Monthly budget: $4.50
- Hard limit: Enable
- Alert threshold: $4.00

### Layer 3: Request Timeouts
Prevents hung connections - lives in FastAPI, not LangGraph state.

**Additions:**
- TimeoutMiddleware in backend/main.py
- Uvicorn timeout flags in docker-compose.yml

### Layer 4: Tool Sandboxing
Prevents tool misuse - uses existing state, adds zero risk.

**Features:**
- Detect SQL injection patterns
- Detect XSS patterns
- Detect JS injection patterns
- Detect shell injection patterns

### Layer 5: Observable-Only Health Checks
Monitors agent health - no new endpoints, no state fields.

**Checks:**
- High tool usage warning (>10 calls)
- Error in memory trace detection
- Infinite loop detection (step > plan.length × 2)

## Critical "Do Nots"

❌ Adding tokens_used to LangGraph AgentState
❌ Persisting tool_calls to Postgres/Redis
❌ Backend-based rate limiting in agent
❌ OpenAI API key rotation in agent code

## Why This Is SNAC v2 Pure

| Layer | Protection | Compliance |
|-------|-----------|------------|
| NGINX Throttling | Network abuse | Zero state mutation |
| OpenAI Budget | Financial | Zero code changes |
| Request Timeouts | Hung connections | Middleware (not agent) |
| Tool Sandboxing | Injection exploits | Uses observables only |
| Health Checks | Failure detection | No new state/fields |

## Validation Commands

```bash
# Test rate limiting
for i in {1..15}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost/agent/health; done

# Test timeout
curl -m 1 https://localhost/agent/health

# Test safety
curl -X POST http://localhost/agent/run -d '{"task":"CALC: 1; DROP TABLE users; --"}' -H "Content-Type: application/json"
```
