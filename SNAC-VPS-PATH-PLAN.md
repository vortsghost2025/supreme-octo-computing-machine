# SNAC VPS Path Reconciliation Plan

**Goal:** Unify the VPS deployment path—resolve planning docs (`/opt/agent-system`) vs actual deployment (`/opt/snac-v2/backend`).

**Current State:**
- **Planning docs (especially 02-architecture-blueprint.md, 15-hostinger-vps-deployment.md):** Reference `/opt/agent-system` as canonical
- **Actual deployment:** Uses `/opt/snac-v2/backend` (from docker-compose files and prior setup)
- **Problem:** Agents + operators get confused which path is "real"

**Decision:** Since actual deployment is already at `/opt/snac-v2/backend` and it's working, **adopt that as canonical and update planning docs to match.**

---

## Current State Inventory

**On Hostinger VPS (187.77.3.56):**

```
/opt/snac-v2/
├── backend/                     ← Actual working path
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── main.py
│   ├── Dockerfile
│   └── (other runtime files)
└── (other directories if present)

# OLD REFERENCE (planning docs only):
/opt/agent-system/              ← PLANNED but not deployed
├── docker-compose.yml          ← In planning docs
├── services/
│   ├── api-gateway/
│   ├── orchestrator/
│   └── cockpit/
└── (never actually deployed)
```

---

## Why Unify?

When deploying or debugging, operators see:

❌ **Confusing scenario:**
```
Ops reads planning doc 15: "Deploy to /opt/agent-system"
Ops SSHes to VPS, finds nothing at /opt/agent-system
Ops finds /opt/snac-v2/backend
Ops wonders: "Is this old? Should I migrate? Which is right?"
Result: Hesitation, delays, uncertainty
```

✓ **After unification:**
```
Ops reads planning doc 15: "Deploy to /opt/snac-v2/backend"
Ops SSHes to VPS, finds /opt/snac-v2/backend
Ops knows: "This is it. This is the one."
Result: Confidence, clear action, fast iteration
```

---

## Plan: 3 Stages

### Stage 1: Update Planning Docs (Local, Immediate)

**Update these files in S:\snac-v2\snac-v2\plans\:**

| File | Line | Current Text | New Text | Reason |
|------|------|--------------|----------|--------|
| 02-architecture-blueprint.md | ~20 | `/opt/agent-system/` | `/opt/snac-v2/backend/` | Reflect actual path |
| 15-hostinger-vps-deployment.md | ~25 | `mkdir -p /opt/agent-system` | `mkdir -p /opt/snac-v2/backend` | Match deployment |
| 15-hostinger-vps-deployment.md | ~27 | `cd /opt/agent-system` | `cd /opt/snac-v2/backend` | Match deployment |
| Any other § mentioning `/opt/agent-system` | (search first) | `/opt/agent-system` | `/opt/snac-v2/backend` | Global unification |

**How to do it:**
```powershell
cd S:\snac-v2\snac-v2
# Search for all mentions
grep -r "/opt/agent-system" plans/
# Replace (will do this with multi-replace below)
```

**Time:** 5 minutes (bulk find-replace)

### Stage 2: Verify VPS Path Structure (Pre-Deployment Check)

Before any deployment, confirm actual VPS structure matches expectations.

**SSH to VPS:**
```bash
ssh root@187.77.3.56
ls -la /opt/snac-v2/backend/
ls -la /opt/snac-v2/  # See what else is there
pwd
df -h /opt            # Check disk space
```

**Expected output:**
```
/opt/snac-v2/backend/:
  docker-compose.yml
  requirements.txt
  main.py
  Dockerfile
  node_modules/ or env/   (runtime artifacts)

/opt/snac-v2/:
  backend/
  (maybe: ui/, workspace/, etc. copied from local)
```

**If path structure is different:**
- Ask: "Should we move it to match local, or document as-is?"
- Update this plan with actual structure
- Do NOT move until user confirms

**If `/opt/agent-system` still exists:**
```bash
ls -la /opt/agent-system
# If it has old files:
mv /opt/agent-system /opt/agent-system-archived-$(date +%Y-%m-%d)
```

### Stage 3: Update Deployment Scripts (Local → VPS)

Once planning docs are updated and VPS structure is verified:

**Update deployment scripts to reference new path:**

**Files that reference paths (search and update):**
- Any `ansible/` playbooks in S:\snac-v2\snac-v2\
- `launch-all.cmd` or similar (if they have VPS references)
- Docker Compose health check URLs (if they mention `/opt/`)
- Environment variable templates (`.env.example`)

**Example update:**
```yaml
# BEFORE
- name: Deploy to /opt/agent-system
  hosts: "{{ vps_host }}"
  tasks:
    - shell: cd /opt/agent-system && docker-compose up -d

# AFTER
- name: Deploy to /opt/snac-v2/backend
  hosts: "{{ vps_host }}"
  tasks:
    - shell: cd /opt/snac-v2/backend && docker-compose up -d
```

---

## Implementation Checklist

**Order matters. Do these in sequence:**

- [ ] **Stage 1: Update planning docs locally**
  - [ ] Search `grep -r "/opt/agent-system" plans/`
  - [ ] Replace all instances in 02-*, 15-*, and any other files
  - [ ] Verify no stray references: `grep -r "opt/agent" plans/` (should be empty)
  - [ ] Commit: `git add plans/; git commit -m "Docs: unify VPS path to /opt/snac-v2/backend"`

- [ ] **Stage 2: Verify VPS structure**
  - [ ] SSH to 187.77.3.56
  - [ ] `ls -la /opt/snac-v2/backend/`
  - [ ] Confirm docker-compose.yml, main.py, Dockerfile exist
  - [ ] Check disk space: `df -h /opt`
  - [ ] If `/opt/agent-system` exists, archive it with timestamp

- [ ] **Stage 3: Update deployment scripts**
  - [ ] Search local repo: `grep -r "/opt/agent" . --include="*.sh" --include="*.yml" --include="*.yaml" --include="*.ps1"`
  - [ ] Update each reference to `/opt/snac-v2/backend`
  - [ ] Commit: `git add .; git commit -m "Deployment: update paths to /opt/snac-v2/backend"`

- [ ] **Final verification:**
  - [ ] `grep -r "opt/agent" .` returns nothing (except this file)
  - [ ] `grep -r "snac-v2/backend" .` shows intended matches only
  - [ ] VPS is reachable: `ssh root@187.77.3.56 'ls /opt/snac-v2/backend'` runs cleanly

---

## Deployment Script Template (Reference)

After unification, deployment from local to VPS should look like:

```bash
# From S:\snac-v2\snac-v2 on Windows, or local Linux
rsync -avz \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=.env \
  ./ root@187.77.3.56:/opt/snac-v2/backend/

ssh root@187.77.3.56 << 'EOF'
  cd /opt/snac-v2/backend
  source .env  # Make sure secrets are loaded
  docker-compose pull
  docker-compose up -d
  docker-compose logs -f --tail=20
EOF
```

---

## Rollback / Undo

If you realize the unification is wrong and `/opt/agent-system` should stay:

1. **Revert commits:**
   ```powershell
   git reset --soft HEAD~2  # Undo last 2 commits
   git checkout HEAD -- plans/  # Restore original docs
   ```

2. **Update VPS back:**
   ```bash
   ssh root@187.77.3.56
   mv /opt/snac-v2/backend /opt/agent-system
   # Update docker-compose references back
   ```

3. **Re-confirm with user** before proceeding

---

## Why This Path, Not Other Options?

**Option A: Keep `/opt/agent-system` (original plan)**
- Pro: Matches planning docs
- Con: VPS is already at `/opt/snac-v2/backend`; moving production is risky
- Decision: Rejected (unnecessarily risky)

**Option B: Move VPS to `/opt/agent-system` (migrate production)**
- Pro: Matches planning docs
- Con: Requires downtime; potential data loss; user has active workloads
- Decision: Rejected (too risky without explicit user need)

**Option C: Standardize on `/opt/snac-v2/backend` (this plan)**
- Pro: Matches actual deployment; no data movement; docs follow reality
- Con: Contradicts original plan (but plan was aspirational, not deployed)
- Decision: Adopted (lowest risk, highest clarity)

---

## Post-Unification Maintenance

Once unified, keep these in sync:

1. **Planning docs** reference `/opt/snac-v2/backend`
2. **docker-compose.yml** on VPS is at `/opt/snac-v2/backend/docker-compose.yml`
3. **Deployment scripts** reference `/opt/snac-v2/backend`
4. **VPS directory structure** stays at `/opt/snac-v2/backend`

**When adding new services/components:**
- Add to S:\snac-v2\snac-v2\backend\docker-compose.yml
- Deploy to `/opt/snac-v2/backend/docker-compose.yml` on VPS
- Update planning docs to reference `/opt/snac-v2/backend`

---

## Timeline

| Stage | Task | Time | Blocker? |
|-------|------|------|----------|
| 1 | Update planning docs | 10 min | No |
| 2 | SSH to VPS + verify | 5 min | No |
| 2 | Archive `/opt/agent-system` if exists | 2 min | No |
| 3 | Search + update deployment scripts | 10 min | No |
| Final | Verify no stray references | 5 min | No |
| **Total** | | **~32 min** | **None** |

---

## Next Step After This Plan

Once Stages 1-3 are complete:

1. User/operator can **confidently reference `/opt/snac-v2/backend`** in all docs and scripts
2. New agents inherit **unified, unambiguous VPS path**
3. Deployment becomes **straightforward:** local → `/opt/snac-v2/backend` → validate
4. Debugging becomes **fast:** "Check `/opt/snac-v2/backend`" is the only path to know

---

## Integration with Other Plans

This plan **depends on** SNAC-REPO-ISOLATION-PLAN (local boundary clarity).  
This plan **informs** future deployment decisions (which path to push code to).

**Read order:**
1. SNAC-REPO-ISOLATION-PLAN (local boundary)
2. SNAC-VPS-PATH-PLAN (VPS boundary)
3. Any future deployment plan (once both are unified)

