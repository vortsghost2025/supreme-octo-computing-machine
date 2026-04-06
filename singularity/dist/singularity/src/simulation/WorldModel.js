/**
 * Simple heuristic‑based world model.
 * It inspects the proposal shape, checks a tiny slice of episodic history
 * and produces a predictive the result used by the orchestrator.
 */
export class WorldModel {
    store;
    bus;
    constructor(store, bus) {
        this.store = store;
        this.bus = bus;
    }
    /**
     * Run a simulation for a proposal.
     * @param proposal   The workflow proposal (shape depends on the adapter)
     * @param confidence Confidence score supplied by the upstream planner
     * @param riskScore  Risk level string (LOW|MEDIUM|HIGH|CRITICAL)
     */
    async simulate(proposal, confidence, riskScore) {
        // --- emit start event ----------------------------------------------------
        const startEvent = {
            id: `simulation-start-${Date.now()}`,
            type: 'simulation.started',
            ts: Date.now(),
            source: 'WorldModel',
            payload: { proposalId: proposal.id },
        };
        this.bus.publish(startEvent);
        // --- basic shape heuristics --------------------------------------------
        const nodeCount = Array.isArray(proposal.nodes) ? proposal.nodes.length : 0;
        const connectionCount = proposal.connections
            ? Object.keys(proposal.connections).length
            : 0;
        const complexity = nodeCount * 2 + connectionCount;
        const hasExternal = Array.isArray(proposal.nodes)
            ? proposal.nodes.some((n) => typeof n.type === 'string' && n.type.includes('external'))
            : false;
        // --- historical context (placeholder – real implementation would read logs) ---
        // For now we just note that we would look at the last 100 episodic entries.
        const basedOnMemoryIds = [];
        // Example: const recent = await this.store.readLast(100);
        // (EpisodicStore currently only supports append, so this is a stub.)
        // --- prediction logic ----------------------------------------------------
        const predictedSuccess = confidence > 0.85 && riskScore !== 'CRITICAL' && complexity < 50 && !hasExternal;
        let predictedRisk = 'LOW';
        if (riskScore === 'HIGH' || riskScore === 'CRITICAL' || complexity > 70 || hasExternal) {
            predictedRisk = 'HIGH';
        }
        else if (riskScore === 'MEDIUM' || complexity > 40) {
            predictedRisk = 'MEDIUM';
        }
        const blastRadius = {
            operational: Math.min(100, complexity * 2),
            dependency: Math.min(100, connectionCount * 3),
            reversibility: Math.max(0, 100 - complexity * 1.5),
            observability: Math.min(100, nodeCount * 2),
        };
        const reasons = [];
        reasons.push(`Node count = ${nodeCount}, connection count = ${connectionCount}`);
        reasons.push(`Complexity score = ${complexity}`);
        reasons.push(`External‑node flag = ${hasExternal}`);
        reasons.push(`Confidence ${(confidence * 100).toFixed(1)}%`);
        reasons.push(`Risk score input = ${riskScore}`);
        reasons.push(`Predicted success = ${predictedSuccess}`);
        reasons.push(`Predicted risk = ${predictedRisk}`);
        const result = {
            proposalId: proposal.id,
            predictedSuccess,
            predictedConfidence: confidence,
            predictedRisk,
            blastRadius,
            reasons,
            basedOnMemoryIds,
        };
        // --- emit completion event --------------------------------------------
        const completedEvent = {
            id: `simulation-complete-${Date.now()}`,
            type: 'simulation.completed',
            ts: Date.now(),
            source: 'WorldModel',
            payload: result,
        };
        this.bus.publish(completedEvent);
        return result;
    }
}
