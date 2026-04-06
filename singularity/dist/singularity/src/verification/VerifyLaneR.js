import { EventBus } from '../bus/EventBus';
import { N8nAdapter } from '../adapters/n8n/N8nAdapter';
/**
 * Verification lane R – runs in isolation from lane L.
 */
export class VerifyLaneR {
    bus = EventBus.get();
    adapter = new N8nAdapter();
    constructor() {
        this.bus.subscribe('governance.proposal.created', (e) => this.handleProposal(e));
    }
    async handleProposal(event) {
        const { proposal } = event.payload;
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
                confidence: event.payload.confidence,
                riskScore: event.payload.riskScore
            }
        });
    }
}
