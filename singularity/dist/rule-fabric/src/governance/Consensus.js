import { EventBus } from '../bus/EventBus';
import { Constitution } from './Constitution';
export class Consensus {
    bus = EventBus.get();
    constitution = new Constitution();
    async decide(proposalEvent) {
        // Run constitution first (policy check)
        await this.constitution.validate(proposalEvent);
        // Wait for lane reports (L & R)
        const laneResults = await Promise.all([
            this.waitForLane('verify.lane.l', proposalEvent.id),
            this.waitForLane('verify.lane.r', proposalEvent.id),
        ]);
        const allPass = laneResults.every(r => r.payload.pass === true);
        if (!allPass) {
            this.bus.publish({
                id: `consensus-${proposalEvent.id}`,
                type: 'governance.consensus.rejected',
                ts: Date.now(),
                source: 'Consensus',
                payload: { proposalId: proposalEvent.id, reason: 'lane disagreement' },
            });
            throw new Error('Consensus rejected');
        }
        // Accepted
        this.bus.publish({
            id: `consensus-${proposalEvent.id}`,
            type: 'governance.consensus.accepted',
            ts: Date.now(),
            source: 'Consensus',
            payload: { proposalId: proposalEvent.id },
        });
        return true;
    }
    waitForLane(topic, proposalId) {
        return new Promise(resolve => {
            const handler = (e) => {
                if (e.payload.proposalId === proposalId) {
                    this.bus.subscribe(topic, () => { }); // remove listener
                    resolve(e);
                }
            };
            this.bus.subscribe(topic, handler);
        });
    }
}
