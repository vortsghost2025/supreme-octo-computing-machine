# PROJECT REVIEW — What This Is & How to Get Kilo Working on a Fresh Windows Install

**Start here if you just got a new PC, reinstalled Windows, or Kilo will not start at all.**

---

## 🔴 CRITICAL: Reinstalling Windows Does NOT Fix Kilo

If Kilo stopped working and you reformatted / reinstalled Windows and it is **still broken**, this is expected. The crash is caused by a problem on the VPS server, not on your PC. Wiping your PC changes nothing on the VPS.

**The fix is always on the server side:**

```powershell
./fix-kilo.ps1
```

Run that one command after you set up your PC (follow the steps below). It logs into the VPS over SSH and removes the stray container that causes the crash.

---

## What This Project Is

This is your personal AI agent system called **SNAC-v2**.

- It runs 24/7 on your Hostinger VPS at IP `187.77.3.56`
- You control it from your Windows PC using the **Kilo Code** VS Code extension
- Your PC is just a remote control — the AI brain lives on the server
- You do not need Docker, Node, or any server software on your PC

---

## Step-by-Step: Set Up a Fresh Windows PC

Do these steps in order. Each one is required before the next.

### Step 1 — Install VS Code

Download and install from: **https://code.visualstudio.com**

Accept all defaults during installation.

---

### Step 2 — Install Git for Windows

Download and install from: **https://git-scm.com/download/win**

Accept all defaults. This lets you pull code from GitHub.

---

### Step 3 — Install the Kilo Code Extension in VS Code

1. Open VS Code
2. Press `Ctrl+Shift+X` to open Extensions
3. Search for **Kilo Code**
4. Click **Install**
5. Restart VS Code when prompted

---

### Step 4 — Clone This Repo

Open a terminal in VS Code (`Ctrl + backtick`) and run:

```powershell
cd C:\Users\YourName\Documents
git clone https://github.com/vortsghost2025/supreme-octo-computing-machine.git
cd supreme-octo-computing-machine
```

Replace `YourName` with your actual Windows username, or clone wherever you want.

---

### Step 5 — Configure Kilo (MCP Settings)

Run this script to put Kilo into the correct mode for this project:

```powershell
./set-kilo-snac-mode.ps1
```

Then reload VS Code: press `Ctrl+Shift+P` → type `Reload Window` → press Enter.

---

### Step 6 — Connect Kilo to an AI Model

Kilo needs to know which AI to use. You have two options — pick one:

**Option A — Use your Claude.ai account (uses your $30/mo subscription, no extra charge)**

1. Open VS Code → click the Kilo panel on the left sidebar
2. Click the settings gear icon
3. Under **API Provider**, choose **Claude** or look for **"Log in with Anthropic"**
4. Sign in with your Claude.ai email and password
5. Leave the **API Key** field empty or blank

This uses your subscription. No per-message charges.

**Option B — Use a local free model with Ollama (zero cost, runs on your PC)**

1. Download Ollama from **https://ollama.com** (free Windows installer)
2. After installing, open a terminal and run:
   ```powershell
   ollama pull llama3.2
   ```
3. In Kilo settings → API Provider → choose **Ollama**
4. Set base URL to `http://localhost:11434`
5. Select the model you downloaded

No API key, no cloud costs, works offline.

> ⚠️ **Do NOT create an Anthropic API key** unless you understand it is pay-per-use and completely separate from your $30/mo Claude subscription. If you were charged unexpectedly before, read [SPENDING-EMERGENCY.md](SPENDING-EMERGENCY.md).

---

### Step 7 — Fix the VPS (This Is Why Kilo Is Broken)

Now that your PC is set up, fix the server:

```powershell
./fix-kilo.ps1
```

This script:
1. SSH-es into your VPS at `187.77.3.56`
2. Removes any stray Docker containers that cause Kilo to crash
3. Resets Kilo's local MCP cache on your PC

After it finishes, reload VS Code (`Ctrl+Shift+P` → `Reload Window`) and Kilo should work.

---

## If Kilo Is Still Broken After All Steps Above

Work through this checklist:

| Check | How to check |
|-------|-------------|
| Is the VPS running? | Open `http://187.77.3.56` in a browser. If it loads, the server is up. |
| Are the containers healthy? | `ssh root@187.77.3.56 "docker compose -f /opt/snac-v2/backend/docker-compose.yml ps"` |
| Is there a stray container? | `ssh root@187.77.3.56 "docker ps --format '{{.Names}}'"` — anything NOT starting with `snac_` is a stray |
| Remove a stray manually | `ssh root@187.77.3.56 "docker stop <name> && docker rm <name>"` |

**Canonical container names** (only these should be running):

```
snac_db        snac_redis      snac_qdrant
snac_backend   snac_frontend   snac_nginx    snac_free_agent
```

If you see anything else, stop it and run `./fix-kilo.ps1` again.

---

## Useful Scripts in This Folder

| Script | What it does |
|--------|--------------|
| `./fix-kilo.ps1` | **Main fix — run this first every time** |
| `./set-kilo-snac-mode.ps1` | Set Kilo to SNAC-only mode (recommended) |
| `./reset-kilo-extension.ps1` | Full Kilo cache wipe — more thorough than fix-kilo |
| `./scripts/emergency-stop-api.ps1` | Blank the API key to immediately stop charges |
| `./set-mcp-local.ps1` | Switch Kilo to local-only MCP |
| `./set-mcp-vps.ps1` | Switch Kilo to VPS-only MCP |

---

## Where Is Everything?

| Thing | Location |
|-------|----------|
| VPS server | Hostinger, IP `187.77.3.56` |
| Cockpit dashboard | `http://187.77.3.56` (open in any browser) |
| Backend API | `http://187.77.3.56:8000` |
| VPS project files | `/opt/snac-v2/backend` (on the VPS) |
| Kilo settings (Windows) | `%APPDATA%\Code\User\globalStorage\kilocode.kilo-code\settings\` |

---

## Common Questions

**Q: I reinstalled Windows and Kilo is still broken.**  
A: Windows reinstall does not affect the VPS. The crash lives on the server. Run `./fix-kilo.ps1` after cloning the repo again (Step 4–7 above).

**Q: Kilo asks for an API key. Do I need one?**  
A: No — use your Claude.ai account login (Option A in Step 6 above) or Ollama (Option B). An API key is pay-per-use and separate from your subscription.

**Q: Does my $30/month subscription cover Kilo?**  
A: Only if you log in with your Claude.ai account credentials inside Kilo (not via an API key). See Step 6 above and [SPENDING-EMERGENCY.md](SPENDING-EMERGENCY.md).

**Q: How do I know if the server is running?**  
A: Open `http://187.77.3.56` in a browser. If you see the cockpit dashboard, the server is up.

**Q: Can I use Kilo without the VPS?**  
A: Yes — Kilo itself is just a VS Code extension. It works as a local AI assistant with Ollama even if the VPS is down. The VPS adds memory/storage features but is not required for basic use.

---

## More Documentation in This Repo

| File | What it covers |
|------|---------------|
| [GETTING-STARTED.md](GETTING-STARTED.md) | Daily usage guide, how to run tasks |
| [SPENDING-EMERGENCY.md](SPENDING-EMERGENCY.md) | Unexpected API charges — how to stop them and get a refund |
| [CRASH-ASSESSMENT.md](CRASH-ASSESSMENT.md) | Technical post-crash analysis |
| [KILO-ISOLATION.md](KILO-ISOLATION.md) | How Kilo's filesystem isolation works |
| [CLINE-SETUP-REFERENCE.md](CLINE-SETUP-REFERENCE.md) | Alternative AI agents if Kilo is not working for you |
| [README.md](README.md) | Full technical overview of the SNAC-v2 system |
