# Planning Document 21: Persistent Memory Bank and Shared Knowledge Dashboard

## Purpose
Capture the reusable architecture ideas from external collaboration while keeping SNAC-v2 isolated from unrelated project domains.

## Non-Contamination Rule
- Exclude all medical-pipeline specific logic, schemas, prompts, and datasets.
- Rebuild IDE/dashboard features from first principles inside SNAC-v2.
- Reuse only platform-level patterns: memory layers, model-to-model sharing, persistent knowledge UI.

## Product Concept
A Persistent AI Environment Dashboard where multiple agents/models can:
- publish learnings
- share learnings across agents
- tag impact and confidence
- route specific memory layers into specific agent runs

## Memory Taxonomy (Stabilization Addendum)

Primary memory classes to preserve across crashes and resets:
- event_memory: swarm lifecycle events and control-plane decisions
- execution_memory: task outputs, durations, and status history
- thought_memory: idea ingestion, clustering metadata, and project mapping
- strategy_memory: optimization decisions, guardrail outcomes, and policy evolution

Storage tiers:
- Redis Streams for hot event and execution continuity
- Qdrant for semantic retrieval and clustering
- Postgres for durable canonical records and audit history

## Core Feature Set

1. Shared Knowledge Feed
- Time-ordered learnings with source model, topic, and detail.
- Supports direct and cross-model shares.

2. Add Learning Form
- Source model
- Topic
- Details
- Impact level
- Confidence

3. Memory Injection Control
- Select memory layers to inject per agent run.
- Injection policies: strict, weighted, or advisory.

4. Persistent Memory Store
- Durable storage in Postgres.
- Fast retrieval index in Redis and vector layer in Qdrant.

## 48-Layer Memory Bank (Practical Mapping)
Instead of hardcoding 48 independent code paths, implement 6 domains x 8 layers.

Domains:
- orchestration
- coding
- research
- review
- operations
- ideas

Layers per domain:
1. scratch
2. short_term
3. working_context
4. verified_patterns
5. historical_decisions
6. cross_model_shared
7. long_term_indexed
8. policy_constraints

Total layers: 6 x 8 = 48

## Data Model (MVP)

Table: memory_entries
- id (uuid)
- domain (text)
- layer (text)
- source_agent (text)
- source_model (text)
- topic (text)
- summary (text)
- details (text)
- impact_level (text)
- confidence (numeric)
- tags (jsonb)
- created_at (timestamp)

Table: memory_links
- id (uuid)
- from_entry_id (uuid)
- to_entry_id (uuid)
- link_type (text)
- score (numeric)
- created_at (timestamp)

Table: memory_injection_policies
- id (uuid)
- target_agent_type (text)
- include_domains (jsonb)
- include_layers (jsonb)
- max_entries (int)
- min_confidence (numeric)
- mode (text)

## API Contracts

1. POST /memory/learn
- Add a new learning entry.

2. GET /memory/feed
- Return recent shared knowledge items.

3. POST /memory/share
- Share one entry from source model/agent to one or many targets.

4. POST /memory/inject/preview
- Show what memories would be injected for a planned run.

5. POST /memory/inject/apply
- Apply memory set to current workflow context.

6. GET /swarm/graph/snapshot
- Return live topology payload for cockpit graph view.

7. GET /swarm/intelligence/summary
- Return aggregate swarm learning metrics and recommended strategy.

8. Stream-backed checkpoint channel (`swarm.checkpoints`)
- Store resumable progress for long-running tasks.

## Cockpit UI Modules

1. Shared Knowledge Panel
- Feed list with source, topic, impact, and timestamp.

2. Add Learning Drawer
- Fast input form with validation.

3. Memory Layer Matrix
- 6 x 8 grid showing enabled/disabled layers per agent.

4. Injection Inspector
- Preview selected memories before run.

## Safety and Quality Rules
- No blind memory injection into all agents.
- Enforce confidence threshold for automatic injection.
- Keep policy_constraints layer immutable except admin actions.
- Write full audit entries when memory is shared or injected.
- Ensure each long-running task emits checkpoints so restarts resume instead of restarting from zero.
- Treat IDE/editor state as non-durable; persistence must live in runtime services.

## Build Sequence

Phase A
- Add memory entry and feed APIs.
- Add minimal cockpit feed + add-learning form.

Phase B
- Add layer metadata and injection preview endpoint.
- Add layer matrix UI.

Phase C
- Add cross-model sharing and links.
- Add policy-based automatic injection.

Phase D
- Add ranking and conflict resolution between memories.

## Definition of Done (MVP)
- New learning can be added and persists.
- Feed shows recent learnings with source attribution.
- Injection preview works per agent type.
- At least one live workflow can run with selected memory layers.

## Current Implementation Alignment (2026-03-12)

Implemented now:
- `POST /memory/learn`
- `GET /memory/feed`
- `POST /memory/share`
- `POST /memory/inject/preview`
- `POST /memory/inject/apply`
- `POST /ingest-thought` (thought ingestion entrypoint that should feed this memory system)

Still to implement for this spec:
- cockpit UI flow for cross-model share actions
- durable Postgres-backed memory entries and links
- explicit 6x8 memory layer matrix policy controls in cockpit
- full audit entries for memory share/injection operations

## Stabilization Priority Updates (2026-03-12)

Next highest-priority implementation tasks:
1. Upgrade swarm events/results/memory traffic to Redis Streams as source of truth.
2. Add checkpoint persistence for resumable long tasks (`swarm.checkpoints`).
3. Implement `/swarm/graph/snapshot` for live cockpit topology.
4. Implement `/swarm/intelligence/summary` for adaptive strategy feedback.
5. Add idea clustering + project assignment pipeline after `/thoughts/ingest`.
