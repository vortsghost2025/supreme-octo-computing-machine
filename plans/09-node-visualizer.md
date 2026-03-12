# Planning Document 9: LangGraph Node Transition Visualizer

## Overview

Drop-in component that transforms agent's internal execution flow into a real-time debugger view of LangGraph state machine.

## Key Features

1. **Zero Backend Changes** - Uses existing state (plan, step, toolCalls, memory)
2. **True Node-Level Visibility** - Shows Planner, Worker nodes, END
3. **Tool Call Sub-Steps** - Each worker shows exact tool usage
4. **Status Clarity** - Color-coded: pending (gray), active (yellow + pulse), completed (green), END (blue)
5. **VPS-Optimized** - Pure frontend derivation

## Components

### cockpit/components/NodeVisualizer.tsx

React component that:
- Derives node transitions from plan, currentStep, toolCalls, memory
- Shows Planner → Worker 1 → Worker 2 → ... → END flow
- Highlights active node with pulse animation
- Shows tool call sub-steps for each worker

### Types

```typescript
export type NodeTransition = {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed';
  description: string;
  icon: string;
  color: 'indigo' | 'yellow' | 'green' | 'gray' | 'blue';
  subSteps?: Array<{
    label: string;
    icon: string;
  }>;
};
```

## Integration

1. Add NodeTransition type to types/index.ts
2. Import into pages/index.tsx
3. Insert <NodeVisualizer /> section

## Example Output

| Node | Status | Description |
|------|--------|-------------|
| Planner | ✅ Completed | Created 2-step plan |
| Worker 1 | ⚡ Active (pulsing) | Executing: QUERY |
| Worker 2 | ⏳ Pending | Pending: CALC |
| END | ⏳ Pending | Task not finished |

## Why This Beats Broadcasting State

- Uses only state LangGraph already commits
- Derives transitions purely from observables
- Keeps backend pure LangGraph
- Makes UI a passive mirror

## Optional Next Steps

1. Token Cost Monitor - cost per turn, daily spend, RAG/tool breakdown
2. n8n Workflow Trigger Panel - active workflows, trigger history
