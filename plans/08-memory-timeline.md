# Planning Document 8: Memory Timeline Component

## Overview

Drop-in enhancement for cockpit that transforms raw `state.memory` into an intuitive, time-ordered visualization of the agent's reasoning journey.

## Key Features

1. **Semantic Memory Tagging** - Auto-detects RAG, TOOL, REASON, LOG from memory strings
2. **Temporal Visualization** - Staggered timestamps show when each memory entry was created
3. **Zero Runtime Cost** - Pure frontend transformation
4. **VPS-Friendly** - No extra dependencies

## Components

### cockpit/components/MemoryTimeline.tsx

React component that:
- Parses memory strings into structured entries
- Categorizes entries by type (RAG, TOOL, REASON, LOG)
- Renders as timeline with icons and colors
- Shows timestamp for each entry

### Types

```typescript
export type MemoryEntry = {
  id: number;
  timestamp: Date;
  content: string;
  type: 'RAG' | 'TOOL' | 'REASON' | 'LOG';
  icon: string;
  color: 'indigo' | 'emerald' | 'violet' | 'gray';
};
```

## Integration

1. Add type to `cockpit/src/types/index.ts`
2. Import into `pages/index.tsx`
3. Replace Memory Trace section with `<MemoryTimeline />`

## Example Output

| Time | Type | Content |
|------|------|---------|
| 14:03:01 | 🔍 RAG | Knowledge base query: "What is the capital of France?" → Result: Paris |
| 14:03:02 | 💭 REASON | Planner created 2-step plan |
| 14:03:03 | ⚙️ TOOL | calculator → Input: "25 * 4" → Output: 100 |
| 14:03:04 | 📝 LOG | Task complete! Final result: 100 |

## Next Steps (Optional)

1. Token Cost Monitor - shows $/turn, daily spend, RAG vs. tool cost breakdown
2. Agent Graph Visualizer - renders LangGraph state machine as nodes + transitions
