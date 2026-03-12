# Agent Boundary Rules

**Purpose:** Prevent agents from duplicating work across overlapping project zones.  
**Scope:** How to direct tasks to the correct isolated project and what agents must NOT do.

---

## Machine Layout (Read-Only Reference)

```
S:\ (drive root)
├── snac-v2/                      ← SNAC PROJECT ZONE
│   └── snac-v2/                  ← SNAC WORKING DIRECTORY (S:\snac-v2\snac-v2)
│       ├── backend/              ← Python FastAPI skeleton ("test" stub)
│       ├── ui/                   ← React/Vite frontend
│       ├── workspace/            ← Orchestrator, clients, scripts
│       ├── plans/                ← Planning docs (1-15)
│       ├── SYSTEM-MAP.md         ← Boundary definitions
│       ├── AGENT-HANDOFF.md      ← Prior agent context
│       └── [git repo root here]  ← After SNAC-REPO-ISOLATION-PLAN.md Stage 5
│
├── workspace/                    ← WORKSPACE PROJECT ZONE (SEPARATE)
│   ├── clients/                  ← SDK clients (gemini, llama, etc.)
│   ├── orchestrator/             ← Alternative orchestrator
│   ├── services/                 ← Database, auth, other services
│   ├── cockpit/                  ← Alternative cockpit UI
│   ├── package.json              ← Root-level dependencies
│   └── [may have its own .git]
│
└── FreeAgent/                    ← FREEAGENT EXPERIMENT (SEPARATE)
    ├── orchestrator/             ← Experimental orchestrator
    ├── gcp_proof.py
    └── [has own .git at this level]

C:\Users\seand\                  ← USER & TOOL STATE
├── AppData\Roaming\Code\User\   ← VS Code user settings, extensions, Kilo config
├── Desktop\, Documents\, etc.   ← User files
└── [browser profiles, caches]   ← Runtime artifacts (in .gitignore)

VPS (Hostinger 187.77.3.56)      ← RUNTIME TRUTH
├── /opt/agent-system/           ← Or /opt/snac-v2/backend (to be unified)
│   └── docker-compose.yml
└── [See SNAC-VPS-PATH-PLAN.md]
```

---

## Agent Routing Matrix

**When user asks for SNAC work, use this table. ONLY in-scope agents modify files.**

| Task Type | Working Directory | Scope Limits | Agent Role | DO THIS | DON'T DO THIS |
|-----------|-------------------|--------------|-----------|---------|---------------|
| **SNAC Code** (backend, UI, orchestrator) | S:\snac-v2\snac-v2 | Read `workspace/orchestrator/`, `workspace/clients/` only if modifying SNAC-specific stubs; can write to S:\snac-v2\snac-v2/* | Default Code Agent | `cd S:\snac-v2\snac-v2; edit files; test locally; read workspace/` | Touch S:\workspace\/*, avoid S:\FreeAgent, do NOT run broad git restore |
| **SNAC Architecture** (planning, design) | S:\snac-v2\snac-v2\plans\ | Read plans/ recursively; write new .md to plans/; reference VPS paths but do NOT deploy yet | Default Code Agent | `cd plans/; read 1-15.md; write 16-*.md; reference VPS` | Do NOT assume plans/ describe current deployments; do NOT edit VPS without separate deploy plan |
| **SNAC VPS Deploy** | Hostinger 187.77.3.56:/opt/agent-system | SSH + Docker Compose only; reference SNAC-VPS-PATH-PLAN | azure-deploy, DevOps Agent (if available) | Use ansible/ssh to apply SNAC-VPS-PATH-PLAN; validate with `docker compose logs; curl /health` | Do NOT move folders; do NOT edit Hostinger non-SNAC zones; do NOT assume local paths match VPS paths |
| **SNAC Repo Isolation** | S:\snac-v2\snac-v2\.git | Execute SNAC-REPO-ISOLATION-PLAN stages 0-5 only; follow rollback steps exactly | Code Agent with Git expertise | Run stages 1-2 (commit + verify deletions); run stage 3-5 when user confirms | Do NOT skip verification steps; do NOT use `git reset --hard HEAD~N` blindly; do NOT delete S:\.git manually before archiving |
| **Workspace Project** (if user explicitly asks) | S:\workspace | Read-only exploration only; NEVER modify without explicit user request and separate boundary confirmation | Explore subagent | `cd S:\workspace; audit structure; report; ask user` | Do NOT commit or push; do NOT assume it's part of SNAC; do NOT delete anything |
| **FreeAgent Project** (if user explicitly asks) | S:\FreeAgent | Read-only exploration only; it has separate .git, is an experiment | Explore subagent | Document as separate experiment; do NOT integrate into SNAC | Do NOT move files; do NOT merge histories |
| **Kilo Extension Config** | C:\Users\seand\AppData\Roaming\Code\User\globalStorage\kilocode.kilo-code\settings\ | Modify only mcp_settings.json to toggle SNAC-mode (use toggle scripts) | Default Code Agent | Use set-kilo-snac-mode.ps1 when working in SNAC; verify with grep | Do NOT edit other Kilo configs; do NOT assume Kilo settings are project-specific (they're global) |
| **Machine Audit** | Read-only scan (no .git modification) | Run audit-machine-layout.ps1 to inventory zones; do NOT delete/move anything | Explore subagent | `./audit-machine-layout.ps1; report zones; ask user before any action` | Do NOT assume duplicates are mistakes; do NOT propose wholesale cleanup without explicit user approval |

---

## Critical Rules (RED FLAGS)

**These commands are FORBIDDEN unless explicitly requested and you've read the context:**

1. **`git restore` or `git checkout` on broad paths**
   - Example: `git restore workspace/` or `git checkout -- S:\`
   - **Reason:** Will delete uncommitted work across project zones
   - **Safe alternative:** `git status` first; understand what the user wants before touching version control

2. **`rm -Recurse` on project root or parent directories**
   - Example: `rm -r S:\snac-v2` or `rm -r S:\workspace`
   - **Reason:** Cannot be undone except from backups
   - **Safe alternative:** Move to archive folder first: `mv S:\workspace S:\workspace-archive-<date>`

3. **Assuming `S:\` is a single project**
   - **Reason:** It's an accidental git root; three zones live under it
   - **Safe alternative:** Treat each zone (`snac-v2`, `workspace`, `FreeAgent`) separately; follow this table

4. **Running broad git operations before SNAC-REPO-ISOLATION-PLAN Stage 5 completes**
   - Example: `git push`, `git rebase -i`, etc. while root is still S:\
   - **Reason:** Affects all three zones at once
   - **Safe alternative:** Wait until repo isolation is done; then push to canonical `S:\snac-v2\snac-v2` remote only

5. **Proposing file moves without understanding S:\, S:\workspace, and S:\FreeAgent are separate**
   - **Reason:** User originally said "organize all this"—which implies clean boundaries, not wholesale consolidation
   - **Safe alternative:** Confirm with user first; propose audit results before moving anything

---

## Task Coaching Examples

### Example 1: User says "Add a new tool to the orchestrator"

✓ **CORRECT:**
```
cd S:\snac-v2\snac-v2
Read: workspace/orchestrator/
Create: workspace/tools/my_new_tool.py
Edit: workspace/orchestrator/server.js to register tool
Test: Start containers locally, verify tool appears
Commit to S:\snac-v2\snac-v2 repo
```

✗ **WRONG:**
```
cd S:\snac-v2  # Wrong dir
Edit: workspace/orchestrator without understanding if it's SNAC copy or workspace/ copy
Push to GitHub without checking which repo is canonical
Assume workspace/ structure matches orchestrator/ structure
```

### Example 2: User says "I have a file in workspace/ that belongs in SNAC"

✓ **CORRECT:**
```
1. Read both: S:\snac-v2\snac-v2\workspace\clients\ AND S:\workspace\clients\
2. Ask: "These look similar. Are they duplicates? Which is canonical?"
3. Wait for user answer
4. Only then: copy/move file under user's explicit approval
5. It becomes part of S:\snac-v2\snac-v2 repo
```

✗ **WRONG:**
```
Assume workspace/ is inferior; delete it
Merge histories without understanding intent
Propose consolidation without user approval
```

### Example 3: User asks to "fix the agent"

✓ **CORRECT:**
```
1. Ask: "Is this the orchestrator at S:\snac-v2\snac-v2\workspace\orchestrator or S:\workspace\orchestrator?"
2. Read SYSTEM-MAP.md to understand which is active
3. Check docker-compose.yml to see which is deployed
4. Modify ONLY the active one
5. Test locally
6. Commit to S:\snac-v2\snac-v2 (after isolation)
```

✗ **WRONG:**
```
Edit both copies (creates confusion)
Assume context from previous agent sessions without reading current state
Propose merging them (structural decision, not yours to make)
```

---

## Post-Isolation Updates (After SNAC-REPO-ISOLATION-PLAN Stage 5)

Once the repo isolation is complete:

- **S:\snac-v2\snac-v2** becomes the **canonical SNAC repo**
- **S:\workspace** and **S:\FreeAgent** remain **isolated experimental zones**
- Future agents working on SNAC **fetch/push only to S:\snac-v2\snac-v2 origin**
- Future agents working on workspace/FreeAgent **must ask user first** (not automatic)

**Update Kilo default:**
```powershell
# After isolation, Kilo can stay in SNAC-mode by default
# Unless user explicitly switches to full-home mode
./set-kilo-snac-mode.ps1  # Keep this as the default
```

---

## Decision Tree for New Agents

Start here when taking work on this machine:

```
User asks to modify code
├─ Is it in S:\snac-v2\snac-v2?
│  ├─ Yes → See SNAC-REPO-ISOLATION-PLAN (check if Stage 5 done)
│  │       Work normally in this repo
│  └─ No → Is it in S:\workspace or S:\FreeAgent?
│     ├─ Yes → Read this boundary rules document
│     │       Read AGENT-HANDOFF.md for context
│     │       Ask user FIRST before modifying
│     └─ No → Probably browser cache or temp file
│            Check .gitignore before touching
│
User asks to organize/cleanup
├─ Run: ./audit-machine-layout.ps1 (read-only)
├─ Report zones and duplicates
├─ Ask user: "Which files should stay, which should be archived?"
├─ Only after user confirms:
│  └─ Create move/archive plan (don't execute yet)
│     Ask user: "Is this order/timing correct?"
│     Then execute with rollback path documented
│
User asks "is this done?" for a past task
├─ Search prior conversation summary
├─ Check AGENT-HANDOFF.md completion status
├─ Read relevant .md files in S:\snac-v2\snac-v2
└─ Report what was done + what remains
```

---

## Reference: Zone Ownership

| Zone | Owner | Purpose | Status | Agent Default |
|------|-------|---------|--------|---|
| S:\snac-v2\snac-v2 | User + Copilot | Active SNAC v2 development | Post-isolation, canonical repo | ✓ Modify freely |
| S:\workspace | User (earlier phase) | Parallel orchestrator/cockpit work | Stable, experimental | ✗ Read-only (ask first) |
| S:\FreeAgent | User (experiment) | GCP proof-of-concept | Archived/completed | ✗ Read-only (exploration only) |
| C:\Users\seand | User + Extensions | Tool state, Kilo config, browser | Runtime | ✓ Modify Kilo config using toggle scripts only |
| Hostinger VPS | User (deployed) | Production runtime (Docker Compose) | Active | ✓ Deploy using SNAC-VPS-PATH-PLAN |

---

## Checklist for New Agents

Before starting any modification work:

- [ ] Read SYSTEM-MAP.md
- [ ] Read AGENT-HANDOFF.md
- [ ] Read this file (AGENT-BOUNDARY-RULES.md)
- [ ] Check if SNAC-REPO-ISOLATION-PLAN Stage 5 is complete: `git rev-parse --show-toplevel` in S:\snac-v2\snac-v2 should return `S:\snac-v2\snac-v2`, not `S:\`
- [ ] If working on SNAC, verify Kilo is in SNAC-mode: `./set-kilo-snac-mode.ps1`
- [ ] Understand which zone you're modifying before touching any file

---

## Questions to Ask User Before Taking Action

1. **"Is this task for the SNAC project (S:\snac-v2\snac-v2) or a separate zone?"**
2. **"Does this modify code, infrastructure, or documentation?"**
3. **"Should I commit changes to git, or leave them as a draft?"**
4. **"If I find unused files (e.g., old agent copies), should I archive or delete them?"**
5. **"After I finish, would you like me to update the VPS or just prepare it locally?"**

---

## Summary

**Rules are NOT constraints. They're navigation aids for safety on an intentionally fragmented machine.**

The goal is to let you work very fast without agents stepping on each other's work or contaminating boundaries. Follow the matrix, check the reference, and ask before destructive operations.

