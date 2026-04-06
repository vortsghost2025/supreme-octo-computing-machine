import { EventBus } from '../bus/EventBus';
import { N8nAdapter } from '../adapters/n8n/N8nAdapter';
/**
 * Verification lane L – isolated from lane R.
 * Listens to proposal creation, validates via the n8n adapter,
 * then publishes a lane result event.
 */
export class VerifyLaneL {
    bus = EventBus.get();
    adapter = new N8nAdapter();
    constructor() {
        // Subscribe once at construction time
        this.bus.subscribe('governance.proposal.created', (e) => this.handleProposal(e));
    }
    async handleProposal(event) {
        const { proposal } = event.payload;
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
                confidence: event.payload.confidence,
                riskScore: event.payload.riskScore
            }
        });
    }
}
