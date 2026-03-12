# SNAC Repo Isolation Plan

**Goal:** Move from accidental git root at `S:\` to clean, intentional root at `S:\snac-v2\snac-v2`.

**Timeline:** Safe execution in 5 reversible stages. No file moves. No data loss.

**Rollback:** Every stage can be reverted with `git reset --hard HEAD` and `git clean -fd`.

---

## Stage 0: Verify Current State (Pre-Flight Check)

**Run this first:**
```powershell
cd S:\snac-v2\snac-v2
git status
git log --oneline -3
git rev-parse --show-toplevel
```

**Expected output:**
- `git status` shows uncommitted changes (code review approvals, isolation toggle files)
- `git rev-parse --show-toplevel` returns `S:/`
- `git log -3` shows recent commits

**If any output is unexpected, STOP and read AGENT-HANDOFF.md before proceeding.**

---

## Stage 1: Commit Approved Changes (Safe Harbor)

All code review approvals from the prior session are ready to commit.

**Approved files:**
- `kilo-launch.cmd` (localhost:5173 auto-open)
- `launch-all.cmd` (process cleanup, new server startups)
- `workspace/clients/geminiClient.js` (model upgrade to gemini-2.0-flash)
- `workspace/orchestrator/server.js` (JSDoc, quote consistency, sync error handling)

**Isolation/stabilization files already committed in prior stage:**
- `.gitignore` additions for browser artifacts
- `SYSTEM-MAP.md`, `KILO-ISOLATION.md`, `MCP-MODES.md`
- `audit-machine-layout.ps1` and toggle scripts

**What to do:**
```powershell
cd S:\snac-v2\snac-v2
git add kilo-launch.cmd launch-all.cmd workspace/clients/geminiClient.js workspace/orchestrator/server.js
git commit -m "Code review approvals: kilo launch improvements, model upgrade, orchestrator consistency"
```

**Verify:**
```powershell
git status  # Should show "nothing to commit, working tree clean"
```

**Rollback if needed:**
```powershell
git reset --soft HEAD~1  # Uncommits last commit, keeps changes in working directory
git checkout HEAD -- .   # Or just redo the commit
```

---

## Stage 2: Verify Large Deletions Scope

Prior session showed large deletions under `workspace/agent1-3`, `workspace/api`, `workspace/backend`.  
**User verbally confirmed intent but it's critical to verify before isolation.**

**Check what's actually staged:**
```powershell
cd S:\snac-v2\snac-v2
git status
git diff --cached --name-status  # Shows what's staged but not committed
git diff --name-status           # Shows unstaged changes
```

**If large deletions appear:**
1. Ask user: "Should I commit these deletions as part of the isolation, or are they still experimental?"
2. If YES: Include in Stage 1 commit with message `Migration: remove agent1-3, api, backend stubs (replaced by orchestrator)`
3. If NO: Keep them unstaged; they'll flow into the new isolated repo

**Rollback:**
```powershell
git reset HEAD <filename>  # Unstages if accidentally staged
```

---

## Stage 3: Create New Repo at S:\snac-v2\snac-v2 (Rebase Anchor Point)

This is the **critical turning point**. We stop treating `S:\` as the repo root.

**Step 3a: Initialize new repo in the working directory**
```powershell
cd S:\snac-v2\snac-v2

# Create a new git repo here
git init

# Point new repo to old commits as a remote
git remote add origin-old file:///S:/  # Points to old drive-root repo

# Fetch all history from old repo
git fetch origin-old main:temp-branch-old-main  # Or whatever your default branch is (check: git symbolic-ref refs/remotes/origin-old/HEAD)

# Rebase onto the old history
git reset --hard temp-branch-old-main

# Clean up temp branch
git branch -d temp-branch-old-main
```

**Verify:**
```powershell
git log --oneline -5  # Should show your familiar commit history
git rev-parse --show-toplevel  # Should now return S:\snac-v2\snac-v2
```

**Rollback: (Most critical—keep terminal window open)**
```powershell
# If anything goes wrong BEFORE closing terminal:
cd S:\snac-v2\snac-v2
rm -Force -Recurse .git
# Then re-clone or reset from backup
```

---

## Stage 4: Verify New Repo Health

**Run all checks:**
```powershell
cd S:\snac-v2\snac-v2

# Check file integrity
git status
git ls-files | wc -l  # Count of tracked files

# Check branch structure
git branch -a
git log --oneline -10

# Check that ignored files are ignored (not deleted from disk)
ls -la node_modules/ 2>$null | head -3  # Should exist
ls -la ui/node_modules/ 2>$null | head -3  # Should exist
ls -la workspace/node_modules/ 2>$null | head -3  # Should exist
```

**What to expect:**
- Working tree clean (or small number of untracked files)
- All node_modules still present on disk (were in `.gitignore`)
- Full commit history preserved
- Branch shows just the new local repo

**If anything looks wrong: Do NOT proceed to Stage 5. Ask before continuing.**

---

## Stage 5: Retire Old Repo (Drive-Root)

Once Stage 4 confirms the new isolated repo is healthy:

**Archive the old repo reference:**
```powershell
# Optional: Create a dated backup
mkdir S:\git-archive-$(Get-Date -Format yyyy-MM-dd)
Copy-Item -Recurse S:\.git S:\git-archive-$(Get-Date -Format yyyy-MM-dd)\.snac-old-git

# Remove the git marker from drive root
rm -Force S:\.git  # This breaks the old accidental repo

# Verify it's gone
git rev-parse --show-toplevel 2>&1  # Should return error from S:\snac-v2\snac-v2 context
```

**Verify from the new repo:**
```powershell
cd S:\snac-v2\snac-v2
git rev-parse --show-toplevel  # Should return S:\snac-v2\snac-v2 (not S:\)
git status  # Should work cleanly
```

**Cleanup the root .gitignore if desired:**
```powershell
# Optional: Move root .gitignore if it served only the old repo
# For now, leaving it is harmless
ls -la S:\.gitignore  # Check if exists
```

---

## Post-Isolation Steps (Do These After Stage 5 Succeeds)

**1. Update Kilo workspace boundary (already done, but verify):**
```powershell
# Your toggle scripts already target S:\snac-v2\snac-v2, so no change needed
./set-kilo-snac-mode.ps1  # Run again to confirm
```

**2. Ask agents to use isolated repo:**
- Change agent mode: "Work on `S:\snac-v2\snac-v2` only for SNAC tasks"
- Leave `S:\workspace` and `S:\FreeAgent` untouched
- (See AGENT-BOUNDARY-RULES.md for details)

**3. Test that CI/CD still works (if you have any):**
```powershell
cd S:\snac-v2\snac-v2
# Run your normal build/test/deploy pipeline
# docker-compose build
# npm run build  (if applicable)
```

**4. Push to GitHub (if using remote):**
```powershell
git remote add origin https://github.com/YOUR-ORG/snac-v2.git  # Use your actual URL
git branch -M main
git push -u origin main
```

---

## Rollback Strategy (Summary)

| Stage | Rollback Method | Difficulty |
|-------|-----------------|-----------|
| Stage 1 (Commit) | `git reset --soft HEAD~1` | Easy |
| Stage 2 (Deletions) | `git reset HEAD <files>` or `git reset --hard HEAD~1` | Easy |
| Stage 3 (Rebase) | `rm -r .git` + re-fetch from `S:\` backup | Medium (keep terminal open) |
| Stage 4 (Verify) | Stop if anything looks wrong; don't proceed to 5 | Failsafe |
| Stage 5 (Retire) | Restore from `S:\git-archive-<date>` | Medium (why we archive first) |

---

## What This Fixes

✓ Clean git history tied to SNAC, not drive root  
✓ Future agents see correct repo boundary  
✓ No risk of contamination from `S:\workspace` or `S:\FreeAgent`  
✓ Kilo and other tools can target single repo cleanly  
✓ Deploy scripts can reference "repo root" unambiguously  

## What This Does NOT Fix (Separate Tasks)

- VPS path unification (use SNAC-VPS-PATH-PLAN.md)
- Duplicate workspace orchestrator (use AGENT-BOUNDARY-RULES.md to prevent re-work)
- Deletion of `S:\workspace` or `S:\FreeAgent` (separate decision, separate plan)

---

## Next Steps

1. **Run Stage 0** (verify current state)
2. **Run Stage 1** (commit approved changes)
3. **Run Stage 2** (check large deletions)
4. **PAUSE** — User confirms intent before Stage 3
5. **Run Stage 3-5** (isolation execution + verification) in one session with terminal window open
6. **Update agent boundary rules** (AGENT-BOUNDARY-RULES.md) so future agents know not to touch old repo zones

**Time estimate:** 30 minutes total, mostly waiting for verification output.

