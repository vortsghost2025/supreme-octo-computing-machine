# Getting Started

**New here? Start with this file.**  
Everything else in the repo is for AI agents or advanced reference.  
This file is for you.

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

## Kilo Crashes When I Send a Message

This is a known issue. Here is the fix, in order.

**Step 1 — Fix the server (run this in a terminal, takes about 10 seconds):**

```bash
ssh root@187.77.3.56 'bash -s' < scripts/vps-remove-stray-containers.sh
```

This removes a rogue container on the VPS that was causing two agent processes to
answer at the same time, which confused Kilo.

**Step 2 — Reset Kilo on your PC (run this in PowerShell):**

```powershell
./reset-kilo-extension.ps1
```

**Step 3 — Reload VS Code:**

`Ctrl+Shift+P` → type `Reload Window` → press Enter

After these three steps, Kilo should work.

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
| `./set-kilo-snac-mode.ps1` | Puts Kilo in SNAC-only mode (recommended default) |
| `./set-kilo-fullhome-mode.ps1` | Gives Kilo access to your whole home folder |
| `./set-kilo-vps-mode.ps1` | Disables local filesystem access in Kilo |
| `./reset-kilo-extension.ps1` | Full Kilo reset — use this when Kilo crashes |
| `./set-mcp-local.ps1` | Switches MCP profile to local-only |
| `./set-mcp-vps.ps1` | Switches MCP profile to VPS-only |

---

## Common Questions

**Q: Do I need Docker on my PC?**  
A: No. Docker runs on the VPS. Your PC only needs VS Code and Kilo.

**Q: Can I break the server by sending messages?**  
A: No. The worst that happens is an error message. The server keeps running.

**Q: I reinstalled Windows and Kilo is broken again.**  
A: Run `./reset-kilo-extension.ps1` in PowerShell and reload VS Code.  
If it still crashes after that, the VPS stray container is likely back.  
Follow the two-step fix in the "Kilo Crashes" section above.

**Q: Where is the live server?**  
A: Hostinger VPS, IP `187.77.3.56`. Cockpit: `http://187.77.3.56`. API: `http://187.77.3.56:8000`.

**Q: I want to understand how everything works.**  
A: Read `README.md` for a technical overview, then the files in the `plans/` folder.

---

## If You Are Stuck

The best way to diagnose a problem:

1. Open the cockpit at `http://187.77.3.56` — if it loads, the server is up
2. Check containers: `ssh root@187.77.3.56 "docker compose -f /opt/snac-v2/backend/docker-compose.yml ps"`
3. Run the triage script: `ssh root@187.77.3.56 'bash -s' < scripts/vps-docker-triage.sh`
4. If Kilo is the problem, run `./reset-kilo-extension.ps1`
