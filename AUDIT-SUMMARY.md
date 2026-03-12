# Audit Summary

This summary is based on the read-only machine audit run from `S:\snac-v2\snac-v2`.

## What Was Confirmed

### 1. Git boundary is wrong
- `S:\` is the current git worktree root
- `S:\snac-v2`
- `S:\snac-v2\snac-v2`
- `S:\workspace`

All of the above resolve upward to `S:\`

### 2. SNAC boundary is narrower than git boundary
- Intended SNAC envelope: `S:\snac-v2`
- Current SNAC working code folder: `S:\snac-v2\snac-v2`
- This is not the same as the current git root

### 3. There are multiple active project zones on S drive
- `S:\snac-v2`
- `S:\workspace`
- `S:\FreeAgent`
- `S:\agents`

These should not be treated as one project.

### 4. `S:\workspace` is a major parallel project zone
It contains:
- `clients`
- `cockpit`
- `cockpit-ui`
- `orchestrator`
- `services`
- `scripts`
- `tasks`
- `UI`

This is likely where repeated rebuilding and cross-contamination comes from.

### 5. `S:\FreeAgent` is real
- It exists
- It contains its own `.git`
- It contains an `orchestrator` directory

This explains why the earlier `FreeAgent` reference was not pure hallucination.

## Most Important Interpretation

The machine does not have one project problem.
It has a boundary problem.

Agents and tools can easily confuse:
- SNAC work in `S:\snac-v2\snac-v2`
- older or parallel work in `S:\workspace`
- other experiments like `S:\FreeAgent`

## Safe Rules Going Forward

1. Treat `S:\snac-v2\snac-v2` as the active SNAC code folder.
2. Treat `S:\workspace` as a separate project area.
3. Treat `S:\FreeAgent` as a separate repo.
4. Do not run whole-drive code review or agent tasks from `S:\`.
5. Do not move or delete anything in `S:\workspace` or `S:\FreeAgent` until canonical ownership is mapped.

## Immediate Next Steps

1. Keep Kilo in SNAC-only mode.
2. Keep review scoped to `S:\snac-v2\snac-v2` unless explicitly auditing another zone.
3. Later, perform repo-boundary repair so SNAC is no longer nested under the accidental `S:\` git root.
4. If a task references `workspace` or `FreeAgent`, treat it as a separate project and confirm intent before editing.

## Notable Limitation

The duplicate signal scan included many `node_modules` package manifests under the SNAC UI folder. That is not useful evidence of duplication by itself. Future scans should exclude `node_modules` for cleaner results.