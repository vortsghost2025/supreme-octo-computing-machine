# Planning Document 12: Token Cost Monitor v2 (Architecture-Compliant)

## Overview

Refined version of Token Cost Monitor that uses 100% existing state (state.toolCalls + state.memory), requiring ZERO backend changes.

## Key Features

1. **Zero Backend Changes** - Uses only existing state from WebSocket
2. **Actionable Cost Attribution** - Shows which tools drive costs
3. **Budget-Proof Alerts** - Visual pulse + color shift at $4.00/$4.50 thresholds
4. **VPS-Lightweight** - Pure frontend calculation (<0.5ms render time)
5. **SNAC v2 Compliant** - UI is passive projection of existing state

## Components

### cockpit/components/TokenCostMonitor.tsx

React component that:
- Takes toolCalls and memory props (existing state)
- Calculates cost based on tool type
- Shows current task cost and daily estimate
- Displays budget alert bar with color-coded warnings

## Cost Model

| Tool | Cost per Use |
|------|--------------|
| RAG Query | $0.00045 |
| Math Tool | $0.00015 |
| Planner Step | $0.00020 |
| Worker Step | $0.00018 |
| Slack | $0.00 |

## Integration

1. Save file to cockpit/components/TokenCostMonitor.tsx
2. Import in pages/index.tsx
3. Insert <TokenCostMonitor /> section

## Budget Alerts

| Daily Estimate | Status |
|----------------|--------|
| < $4.00 | ✅ Within safe limits |
| $4.00 - $4.50 | 🟡 Approaching limit (pulse) |
| > $4.50 | 🔴 HIGH USAGE (strong pulse) |

## Why This Beats Backend Tracking

- Uses only committed state (tool_calls + memory)
- Derives costs purely from observables
- Keeps backend pure LangGraph
- Makes UI a passive mirror
