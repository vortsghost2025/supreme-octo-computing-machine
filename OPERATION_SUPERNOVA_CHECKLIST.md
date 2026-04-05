# Operation Supernova Checklist (Extended)

## Existing Steps
- [ ] Initialize memory layers
- [ ] Load proposal from global work tier
- [ ] Dispatch to verification lanes (L & R)
- [ ] Aggregate consensus
- [ ] Execute workflow
- [ ] Cleanup resources

## New n8n Integration Steps
- [ ] **Pull** the proposed workflow from n8n (`pullWorkflow(id)`).
- [ ] **Validate** the workflow schema using `validateWorkflow(json)`. Store `schemaValid`.
- [ ] **Risk Scoring** – invoke `getRiskScore()` from the circuit‑breaker module and attach `riskScore`.
- [ ] **Verification Report** – each lane records `{ confidence, riskScore, schemaValid }`.
- [ ] **Consensus** – aggregate reports; require `confidence ≥ 85%`, `riskScore` ≤ `MEDIUM`, and `schemaValid === true`.
- [ ] **Push** the approved workflow to n8n via `pushWorkflow(id, json)`.
- [ ] **Dry‑run** execution (`runDry(id)`).
- [ ] **Rollback** – if dry‑run fails, trigger rollback within a 5‑minute window.
- [ ] **Memory Logging** – write proposal, verification reports, and execution outcomes to `.kilo/memory/*.jsonl`.

## Post‑Execution
- [ ] Log final status to memory layer.
- [ ] Notify global work tier of success/failure.
- [ ] Archive temporary files.
