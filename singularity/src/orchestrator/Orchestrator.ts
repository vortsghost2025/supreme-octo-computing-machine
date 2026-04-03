import { EventBus, EventEnvelope } from '../bus/EventBus';
import { Consensus } from '../governance/Consensus';
import { EpisodicStore } from '../memory/EpisodicStore';
import { N8nAdapter } from '../adapters/n8n/N8nAdapter';
import { VerifyLaneL } from '../verification/VerifyLaneL';
import { VerifyLaneR } from '../verification/VerifyLaneR';
import { RedTeamAgent } from '../security/RedTeamAgent';

/**
 * Central orchestrator – wires proposal flow through:
 *   1️⃣ Constitution (via Consensus)
 *   2️⃣ Dual verification lanes (L & R)
 *   3️⃣ Red‑Team attacks (optional)
 *   4️⃣ Final adapter push
 *   5️⃣ Episodic logging
 */
export class Orchestrator {
  private bus = EventBus.get();
  private consensus = new Consensus();
  private store = new EpisodicStore();
  private n8n = new N8nAdapter();

  // instantiate lane services & red‑team so they start listening immediately
  private laneL = new VerifyLaneL();
  private laneR = new VerifyLaneR();
  private redTeam = new RedTeamAgent();

  constructor() {
    this.bus.subscribe('governance.proposal.created', (e) => this.handleProposal(e));
  }

  private async handleProposal(event: EventEnvelope) {
    // Record incoming proposal
    await this.store.append({ type: 'proposal', payload: event.payload });
    try {
      // Run constitution + dual‑lane verification + consensus
      await this.consensus.decide(event);
      // If consensus succeeds, push to the real adapter (n8n in this demo)
      await this.n8n.push(event.payload);
      await this.store.append({ type: 'deployment', proposalId: event.id, status: 'pushed' });
    } catch (err) {
      // any rejection (rule, lane, consensus) lands here
      await this.store.append({ type: 'deployment', proposalId: event.id, status: 'rejected', error: (err as Error).message });
    }
  }
}
