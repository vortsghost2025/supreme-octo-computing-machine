# Planning Document 4: Critical Fixes and Refinements

## Overview of Fixes Applied

1. **Redis URL Port Fix** - Corrected port 6333 to 6379
2. **OLLAMA Env Var Unification** - Matching keys between .env and docker-compose
3. **RAG Initialization Time Bomb Fix** - Using @lru_cache for better performance
4. **Calculator Tool Safety Upgrade** - More secure calculator with sandboxed eval
5. **n8n Workflow Binding Best Practice** - Using Docker volumes instead of bind mounts

## Impact Summary

| Issue | Risk if Unfixed | Fix Effort | Production Impact |
|-------|-----------------|------------|-------------------|
| Redis port | ❌ Orchestrator/API gateway fails to start | 10 sec | **Blocks entire system** |
| OLLAMA key mismatch | ❌ Agent crashes when using local LLM | 15 sec | Breaks offline capability |
| RAG per-query init | ⚠️ 10-30s latency/query → VPS OOM under load | 2 min | **Makes system unusable at scale** |
| Calculator tool | ⚠️ Potential RCE via crafted input (low prob but real) | 3 min | Security liability |
| n8n workflow bind | ⚠️ Workflow edits lost; drift between UI/code | 1 min | Silent data loss |

## Validation Checklist

Run these **in order** – each step should pass before moving to the next:

| Command | Expected Output | Failure Indicator |
|---------|-----------------|-------------------|
| `docker compose up -d postgres redis qdrant` | All show `healthy` in `docker compose ps` | `unhealthy` or `exit 1` |
| `docker compose logs postgres` | `database system is ready to accept connections` | `FATAL: could not create lock file` |
| `docker compose up -d api-gateway` | `Uvicorn running on http://0.0.0.0:8000` | `Address already in use` or `ModuleNotFoundError` |
| `curl -s http://localhost:8000/health` | `{"status":"ok"}` | `502` or connection refused |
| `docker compose up -d orchestrator` | No traceback in `docker compose logs -f orchestrator` | `KeyError: 'OLLAMA_BASE_URL'` or `ImportError` |
| `curl -X POST http://localhost:8000/agent/run -d '{"task":"What is 2+2?"}' -H "Content-Type: application/json"` | Returns `{"result": "4.0", ...}` | `500` with tool error or `None` result |

## 5-Minute Action Plan

1. Apply the 5 fixes above (copy-paste from previous document)
2. Run:
   ```bash
   docker compose down -v  # Clears volumes for clean state (keep .env!)
   docker compose up -d postgres redis qdrant
   # Wait for healthy logs (20 sec)
   docker compose up -d api-gateway orchestrator cockpit
   ```
3. Test with:
   ```bash
   # Ingest a test doc (creates collection)
   curl -X POST http://localhost:8000/ingest \
     -F "file=@/path/to/test.txt"  # Any small text file
   
   # Query agent
   curl -X POST http://localhost:8000/agent/run \
     -H "Content-Type: application/json" \
     -d '{"task":"What does the test document say about [topic]?"}'
   ```
4. **Watch the magic:**
   ```bash
   docker compose logs -f orchestrator  # See planner → worker → tool calls in real-time
   ```
