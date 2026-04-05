import { EventBus, EventEnvelope } from './bus/EventBus.js';
import { Orchestrator } from './orchestrator/Orchestrator.js';

// bootstrap the orchestrator – this also starts verification lanes and red‑team
new Orchestrator();

const bus = EventBus.get();

/**
 * Helper to submit a proposal into the system.
 * `riskScore` should be one of 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'.
 */
function submitProposal(id: string, proposal: any, confidence: number, riskScore: string) {
  const ev: EventEnvelope = {
    id,
    type: 'governance.proposal.created',
    ts: Date.now(),
    source: 'demo',
    payload: {
      proposalId: id,
      proposal,
      confidence,
      riskScore,
      // placeholders for lane results – actual lanes will publish later
      laneL: true,
      laneR: true
    }
  };
  bus.publish(ev);
}

// Demo proposals
submitProposal('wf-123', { id: 'wf-123', nodes: [], connections: {} }, 0.92, 'LOW'); // should pass all rules
submitProposal('wf-124', { id: 'wf-124', nodes: [], connections: {} }, 0.95, 'CRITICAL'); // high risk -> rejected by constitution
