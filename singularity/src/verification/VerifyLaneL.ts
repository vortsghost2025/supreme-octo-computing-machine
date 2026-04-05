import { EventBus, EventEnvelope } from '../bus/EventBus.js';
import { N8nAdapter } from '../adapters/n8n/N8nAdapter.js';

/**
 * Verification lane L – isolated from lane R.
 * Listens to proposal creation, validates via the n8n adapter,
 * then publishes a lane result event.
 */
export class VerifyLaneL {
  private bus = EventBus.get();
  private adapter = new N8nAdapter();

  constructor() {
    // Subscribe once at construction time
    this.bus.subscribe('governance.proposal.created', (e) => this.handleProposal(e));
  }

  private async handleProposal(event: EventEnvelope) {
    const { proposal } = event.payload as any;
    // Call the adapter's validate method – returns {valid:boolean}
    const validation = await this.adapter.validate(proposal);
    const pass = validation.valid;
    // Publish lane L result
    this.bus.publish({
      id: `verify-l-${event.id}`,
      type: 'verify.lane.l',
      ts: Date.now(),
      source: 'VerifyLaneL',
      payload: {
        proposalId: event.id,
        pass,
        lane: 'L',
        // Pass through confidence and riskScore for downstream use
        confidence: (event.payload as any).confidence,
        riskScore: (event.payload as any).riskScore
      }
    });
  }
}
