# Convoy & Bead Guidelines for SNAC/Singularity Project

## Convoy Design
- **Default: One convoy per PR-sized outcome** (tightly coupled changes that must land together)
- Use **one convoy per theme** only when beads truly depend on each other (e.g., all lint fixes need to happen before all tests)
- Use `merge_mode: "review-and-merge"` so each bead lands independently

## Bead Granularity
- **Rule: One bead = one file/directory that no other bead touches**
- Check for collision: `git status` before slinging
- Example: `"Fix ESLint config in ui/"` and `"Fix TypeScript errors in src/"` = 2 separate beads
- For npm monorepos: **one bead per package** to avoid lockfile conflicts

## Merge/Review Policy (Definition of Done)
Each bead should include:
- `git status` clean (no uncommitted)
- Tests pass: `npm test` or equivalent
- Branch follows pattern: `gt/agent-name/bead-id`
- Run before completing: `gt_list_beads --status in_review`

## Human Handoff Pattern
Create a report file in the repo:
```bash
# After bead completes, in the browse directory:
git log --oneline HEAD~3..HEAD > reports/bead-XXX-outcome.txt
git diff HEAD~3..HEAD > reports/bead-XXX-diff.txt
```
Polecat can do this as final step.

## 48-Hour Priority Queue
1. **"Infrastructure"** - docker-compose, npm workspaces, CI setup
2. **"Core Tests"** - get test suite passing in CI
3. **"Lint & Format"** - ESLint + Prettier integration

## Gotchas for Windows/Tailscale/npm
- Use forward slashes in paths in bead descriptions
- For VPS SSH: include `workdir: "S:\\path\\to\\repo"` in commands
- For npm: include `npm ci` (not `npm install`) for deterministic builds
- Example bead: `"Fix npm workspace: cd ui && npm run build"`

## Example gt Commands

```bash
# Sling a single task
gt_sling --rig_id <rig-id> --title "Fix ESLint config in ui/"

# Sling multiple independent tasks (parallel)
gt_sling_batch --rig_id <rig-id> --convoy_title "UI Fixes" --tasks '[
  {"title": "Fix ESLint in ui/"},
  {"title": "Fix TypeScript in src/"},
  {"title": "Update package-lock.json"}
]' --parallel true
```