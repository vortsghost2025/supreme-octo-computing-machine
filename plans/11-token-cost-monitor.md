# Planning Document 11: Token Cost Monitor

## Overview

Drop-in component that calculates costs purely from existing state (state.toolCalls and state.memory), requiring ZERO backend changes.

## Key Features

1. **Zero Backend Changes** - Uses only existing state from WebSocket
2. **Actionable Cost Attribution** - Shows which tools drive costs (RAG, Math, Planner, Worker)
3. **Budget-Proof Alerts** - Visual pulse + color shift when daily estimate >$4.00/$4.50
4. **VPS-Lightweight** - Pure frontend calculation (<0.5ms render time)
5. **SNAC v2 Compliant** - UI is passive projection of existing state

## Components

### cockpit/components/TokenCostMonitor.tsx

React component that:
- Takes toolCalls and memory props (existing state)
- Calculates cost based on tool type (RAG, Math, Planner, Worker)
- Shows current task cost and daily estimate
- Displays budget alert bar with color-coded warnings

## Cost Model

| Tool | Cost per Use |
|------|--------------|
| RAG Query | $0.00045 |
| Math Tool | $0.00015 |
| Planner Step | $0.00020 |
| Worker Step | $0.00018 |
| Slack (Free) | $0.00 |

## Integration

1. Save file to cockpit/components/TokenCostMonitor.tsx
2. Import in pages/index.tsx
3. Insert <TokenCostMonitor /> section

## Example Output

- Current Task Cost: ~$0.0012
- Daily Estimate: ~$1.15 (at 4 tasks/hour)
- Breakdown Table: Lists each tool type with count + cost

## Budget Alerts

| Daily Estimate | Status |
|----------------|--------|
| < $4.00 | ✅ Within safe limits |
| $4.00 - $4.50 | 🟡 Approaching limit |
| > $4.50 | 🔴 HIGH USAGE |

## Why This Beats Backend Tracking

- Uses only committed state (tool_calls + memory)
- Derives costs purely from observables
- Keeps backend pure LangGraph
- Makes UI a passive mirror
