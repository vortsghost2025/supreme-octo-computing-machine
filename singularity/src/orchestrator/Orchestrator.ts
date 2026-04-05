import { EventBus, EventEnvelope } from '../bus/EventBus.js';
import { Consensus } from '../governance/Consensus.js';
import { EpisodicStore } from '../memory/EpisodicStore.js';
import { N8nAdapter } from '../adapters/n8n/N8nAdapter.js';
import { VerifyLaneL } from '../verification/VerifyLaneL.js';
import { VerifyLaneR } from '../verification/VerifyLaneR.js';
import { RedTeamAgent } from '../security/RedTeamAgent.js';
import { GpuEngine } from '../gpu/GpuEngine.js';

/**
 * Central orchestrator – wires proposal flow through:
 *   1️⃣ Constitution (via Consensus)
 *   2️⃣ Dual verification lanes (L & R)
 *   3️⃣ Red‑Team attacks
 *   4️⃣ Optional GPU kernel execution
 *   5️⃣ Final adapter push (n8n) and episodic logging
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
  private gpuEngine = new GpuEngine();

  constructor() {
    this.bus.subscribe('governance.proposal.created', (e) => this.handleProposal(e));
  }

  private async handleProposal(event: EventEnvelope) {
    // Record incoming proposal
    await this.store.append({ type: 'proposal', payload: event.payload });
    try {
      // Run constitution + lane verification + consensus (includes red‑team)
      await this.consensus.decide(event);

      // Optional GPU stage – if payload asks for it
      const payload = event.payload as any;
      if (payload.requiresGpu && payload.gpuKernel) {
        const gpuOutput = await this.gpuEngine.runKernel(payload.gpuKernel);
        await this.store.append({
          type: 'gpu_execution',
          proposalId: event.id,
          kernel: payload.gpuKernel,
          output: gpuOutput.trim()
        });
      }

      // After all checks, push to the real adapter (n8n in this demo)
      await this.n8n.push(event.payload);
      await this.store.append({ type: 'deployment', proposalId: event.id, status: 'pushed' });
    } catch (err) {
      // any rejection (rule, lane, red‑team, GPU compile error) lands here
      await this.store.append({
        type: 'deployment',
        proposalId: event.id,
        status: 'rejected',
        error: (err as Error).message
      });
    }
  }
}
