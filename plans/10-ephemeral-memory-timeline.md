# Planning Document 10: Ephemeral Memory Timeline (Architecture-Compliant)

## Overview

The ONLY correct Memory Timeline component that uses 100% existing ephemeral state from LangGraph.

## Key Features

1. **Uses Only Existing State** - Takes `state.memory: string[]` from LangGraph
2. **Zero Backend Changes** - No new APIs, no DB, no conversation IDs
3. **Pure Frontend Transformation** - 60 lines of React, zero dependencies
4. **SNAC v2 Compliant** - UI observes backend truth, never invents state
5. **VPS-Lightweight** - Runs in <1ms on $5 VPS

## Components

### cockpit/components/EphemeralMemoryTimeline.tsx

React component that:
- Takes `memories: string[]` prop (existing state)
- Uses heuristic-based typing (PLAN, STEP, TOOL, RESULT, LOG)
- Renders as timeline with icons and colors
- Uses exactly what backend already sends via WebSocket

## Integration

1. Save file to cockpit/components/EphemeralMemoryTimeline.tsx
2. Import in pages/index.tsx
3. Replace existing Memory Trace section with <EphemeralMemoryTimeline />

## Example Output

| Type | Content |
|------|---------|
| 🧠 PLAN | Planner created 2-step plan |
| ⚡ STEP | Worker executed step 1 |
| ⚙️ TOOL | query_knowledge_base → Input → Output |
| 🏁 RESULT | Final result: 25.0 |

## Why This Is Architecture-Pure

- Uses only existing ephemeral state (task-scoped)
- No conversation IDs (timeline resets per /agent/run)
- No polling (uses existing WebSocket memory updates)
- No state invention (only visualizes what LangGraph commits)

## Philosophical Win

> "Your UI should be a mirror, not a mold."

This component proves memory is truly ephemeral - restart agent → timeline clears. No hidden persistence.

## Optional Next Steps

1. Token Cost Monitor - uses existing state.toolCalls + state.memory
2. LangGraph Node Visualizer - uses state.plan, state.step, state.toolCalls
