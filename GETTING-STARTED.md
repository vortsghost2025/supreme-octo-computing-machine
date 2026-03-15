# Getting Started

---

## 🔴 KILO NOT WORKING? FIX IT IN ONE COMMAND

**If Kilo crashes when you send a message, run this first.  
This is the most common problem and this fixes it.**

Open a terminal in VS Code (`Ctrl + backtick`) and run:

```powershell
./fix-kilo.ps1
```

Then press `Ctrl+Shift+P` → type `Reload Window` → press Enter.

That is it. The script handles everything.

**Why it crashes:** A rogue Docker container on your VPS sends duplicate responses to Kilo.  
The `@swarm` mode (5 parallel agents) makes this 5× worse. The script removes the rogue  
container and resets Kilo's local settings.

**If `fix-kilo.ps1` cannot reach the VPS over SSH**, do this manually:

```powershell
ssh root@187.77.3.56
# once connected:
docker ps                           # look for anything NOT in the list below
# canonical containers: snac_db  snac_redis  snac_qdrant  snac_backend  snac_frontend  snac_nginx
docker stop <any-extra-name> && docker rm <any-extra-name>
exit
```

Then run `./fix-kilo.ps1` again (it will still reset Kilo's local settings even without SSH).

---

## ⚠️ API COSTS — READ THIS BEFORE USING KILO

**Your $30/month Claude Pro subscription does NOT cover Kilo's API calls.**  
They are two completely separate billing accounts.

| What you pay | What it covers |
|---|---|
| Claude.ai $30/mo subscription | claude.ai website only |
| Anthropic API key (pay-per-use) | Kilo Code — billed per message |

- If Kilo is configured with an API key, **every message costs money** on top of your subscription.
- `@swarm` spawns 5 agents simultaneously — 5× the API calls, 5× the cost.
- A $10/month hard limit on your API account at **https://console.anthropic.com → Billing → Spending Limits** prevents surprise charges.
- If you were charged unexpectedly, read **[SPENDING-EMERGENCY.md](SPENDING-EMERGENCY.md)**.

---

## What Is This?

This is your personal AI agent system called **SNAC-v2**.  
It is already running on your Hostinger VPS server.  
You do not need to install a server or set anything up from scratch.

What it does:

- Lets you send tasks to an AI agent and see it work step-by-step
- Stores and searches documents you give it (RAG / memory)
- Shows you a real-time dashboard (the "Cockpit") with a timeline, workflow graph, and cost tracker
- Runs 24/7 on your VPS whether your PC is on or not

---

## What You Need on Your Windows PC

1. **VS Code** — already installed  
2. **Kilo Code extension** — already installed (it is the AI assistant inside VS Code)  
3. **Git** — for pulling code changes from GitHub  
4. Nothing else needs to be installed to *use* the system

---

## How to Open the Cockpit (Dashboard)

The cockpit is a webpage that shows what the agent is doing.

Open any browser and go to:

```
http://187.77.3.56
```

You will see three panels:

- **Memory Timeline** — a log of every action the agent has taken
- **Node Visualizer** — shows the workflow graph as the agent runs a task
- **Token Cost Monitor** — shows how many API tokens have been used and what it cost

That is it. The cockpit is read-only. You do not need to log in.

---

## How to Use the Agent (via Kilo in VS Code)

Kilo is the VS Code extension you use to talk to the agent.

**Before you send a message, do this once:**

1. Open a PowerShell terminal inside VS Code (`Ctrl + backtick`)
2. Run this command to put Kilo in the correct mode:
   ```powershell
   ./set-kilo-snac-mode.ps1
   ```
3. Reload VS Code: press `Ctrl+Shift+P`, type `Reload Window`, press Enter

**Then you can send messages normally inside Kilo.**

---

## Using the Parallel Modes (@swarm, @coder, etc.)

Kilo has custom modes like `@architect`, `@coder`, `@debugger`, `@reviewer`, `@orchestrator`.

**Important — use `@swarm` carefully:**  
`@swarm` launches all 5 modes at the same time. This costs 5× the API tokens in one go.  
Use it only for big, deliberate tasks — not for quick questions.

**Safe daily use:** `@coder`, `@debugger`, or `@reviewer` alone (one mode, one agent).

---

## Checking That the Server Is Running

Run either of these in a terminal to check the live server:

```bash
# See all running containers
ssh root@187.77.3.56 "cd /opt/snac-v2/backend && docker compose ps"

# Quick health check
ssh root@187.77.3.56 "curl -fsS http://localhost:8000/health"
```

If the health check prints `{"status":"ok"}` (or similar), the server is fine.

---

## Quick Reference: Scripts in This Folder

These PowerShell scripts are in the root of the project.  
Run them in a VS Code terminal when you need them.

| Script | What it does |
|--------|--------------|
| `./fix-kilo.ps1` | **Fix Kilo crashing — run this first** |
| `./set-kilo-snac-mode.ps1` | Puts Kilo in SNAC-only mode (recommended default) |
| `./set-kilo-fullhome-mode.ps1` | Gives Kilo access to your whole home folder |
| `./set-kilo-vps-mode.ps1` | Disables local filesystem access in Kilo |
| `./reset-kilo-extension.ps1` | Full Kilo reset — more thorough version of fix-kilo |
| `./set-mcp-local.ps1` | Switches MCP profile to local-only |
| `./set-mcp-vps.ps1` | Switches MCP profile to VPS-only |
| `./scripts/emergency-stop-api.ps1` | Blanks API key immediately to stop charges |

---

## Common Questions

**Q: I ran `./fix-kilo.ps1` but it still crashes.**  
A: SSH to the VPS manually and check: `docker ps` — if you see any container name that is NOT one of `snac_db snac_redis snac_qdrant snac_backend snac_frontend snac_nginx`, stop and remove it. Then run `./fix-kilo.ps1` again.

**Q: Do I need Docker on my PC?**  
A: No. Docker runs on the VPS. Your PC only needs VS Code and Kilo.

**Q: Does my $30/month Claude subscription cover Kilo?**  
A: No. Read the API Costs section above and [SPENDING-EMERGENCY.md](SPENDING-EMERGENCY.md).

**Q: I reinstalled Windows and Kilo is broken again.**  
A: The problem is on the VPS, not your PC. Run `./fix-kilo.ps1`.

**Q: Where is the live server?**  
A: Hostinger VPS, IP `187.77.3.56`. Cockpit: `http://187.77.3.56`. API: `http://187.77.3.56:8000`.

**Q: I want to understand how everything works.**  
A: Read `README.md` for a technical overview, then the files in the `plans/` folder.

---

## If You Are Stuck

The best way to diagnose a problem:

1. Run `./fix-kilo.ps1` first
2. Open the cockpit at `http://187.77.3.56` — if it loads, the server is up
3. Check containers: `ssh root@187.77.3.56 "docker compose -f /opt/snac-v2/backend/docker-compose.yml ps"`
4. Run the triage script: `ssh root@187.77.3.56 'bash -s' < scripts/vps-docker-triage.sh`

