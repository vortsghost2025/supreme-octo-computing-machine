# Kilo Code MCP Capabilities Guide

## ⚠️ HOSTINGER ISSUE
The Hostinger MCP crashes when using alwaysAllow. You need to click approval for each call. This is a bug/limitation of this specific MCP server.

---

## CURRENT WORKAROUND

### For VPS Operations
Use SSH directly instead of MCP:
```bash
ssh root@187.77.3.56
docker compose -f /opt/snac-v2/backend/docker-compose.yml ps
```

---

## MCPs THAT WORK WITH alwaysAllow

These MCP servers support auto-approval:
- filesystem
- github  
- brave-search
- fetch
- postgres
- sqlite

---

## WHAT I CAN ADD WITHOUT APPROVAL

Just tell me "add filesystem MCP" and I configure it. These don't need per-call approval:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\Users\\seand"]
    }
  }
}
```

---

## YOUR VPS (187.77.3.56) - Current Status

| Service | Port | Status |
|---------|------|--------|
| snac_backend | 8000 | Running |
| snac_frontend | 3000 | Running |
| snac_db | 5432 | Running |
| snac_redis | 6379 | Running |
| snac_qdrant | 6333-34 | Running |
| snac_n8n | 5678 | Running |
| snac_nginx | 80 | Running |

---

## WHAT'S NEXT

For VPS, you'll need to click approve OR use SSH directly.
For new MCPs (filesystem, github, etc), I can add them without approvals.

Want me to add filesystem MCP?
