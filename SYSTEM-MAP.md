# System Map

This file defines the intended boundaries for this machine.

## Primary Zones

### C Drive
- User profile
- VS Code settings and extension storage
- Kilo and Copilot caches
- Browser and tool runtime state
- Do not treat this as project source by default

### S Drive
- Active projects and experiments
- `S:\snac-v2\snac-v2` is the current SNAC working code folder
- `S:\snac-v2` is the project envelope for SNAC
- Do not use `S:\` itself as a project root

### VPS
- Runtime truth for deployed SNAC Docker services
- Plans describe desired architecture
- VPS containers describe actual deployed architecture

## SNAC Boundaries

### Intended project boundary
- `S:\snac-v2\snac-v2`

### Current accidental git boundary
- `S:\`

### Consequence
- Tools that review from git root can see unrelated files on the drive
- MCP workspace and git workspace are currently misaligned

## Working Rules

1. Keep Kilo in SNAC-only mode while working on this repo.
2. Treat browser caches, profiles, logs, and debug outputs as runtime artifacts.
3. Do not move folders on `S:` or `C:` until duplicates and ownership are mapped.
4. Review app code from the intended project boundary, not from drive root.

## Cleanup Order

1. Contain boundaries
2. Audit duplicates and drift
3. Decide canonical project paths
4. Only then move or delete anything