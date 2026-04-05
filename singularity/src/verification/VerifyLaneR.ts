import { EventBus, EventEnvelope } from '../bus/EventBus.js';
import { N8nAdapter } from '../adapters/n8n/N8nAdapter.js';

/**
 * Verification lane R – runs in isolation from lane L.
 */
export class VerifyLaneR {
  private bus = EventBus.get();
  private adapter = new N8nAdapter();

  constructor() {
    this.bus.subscribe('governance.proposal.created', (e) => this.handleProposal(e));
  }

  private async handleProposal(event: EventEnvelope) {
    const { proposal } = event.payload as any;
    const validation = await this.adapter.validate(proposal);
    const pass = validation.valid;
    this.bus.publish({
      id: `verify-r-${event.id}`,
      type: 'verify.lane.r',
      ts: Date.now(),
      source: 'VerifyLaneR',
      payload: {
        proposalId: event.id,
        pass,
        lane: 'R',
        confidence: (event.payload as any).confidence,
        riskScore: (event.payload as any).riskScore
      }
    });
  }
}
