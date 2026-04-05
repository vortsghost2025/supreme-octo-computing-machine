import { EventBus, EventEnvelope } from '../bus/EventBus.js';

/** Simple vulnerability interface */
interface Vulnerability {
  type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  details: string;
  mitigation: string;
}

/**
 * RedTeamAgent – runs simulated attacks on each proposal.
 * For demonstration it flags any proposal with riskScore HIGH or CRITICAL as a critical injection.
 */
export class RedTeamAgent {
  private bus = EventBus.get();

  constructor() {
    this.bus.subscribe('governance.proposal.created', (e) => this.analyze(e));
  }

  private async analyze(event: EventEnvelope) {
    const { riskScore } = event.payload as any;
    const vulnerabilities: Vulnerability[] = [];

    if (riskScore === 'HIGH' || riskScore === 'CRITICAL') {
      vulnerabilities.push({
        type: 'injection',
        severity: 'CRITICAL',
        details: 'Mock injection vulnerability detected for high risk proposal',
        mitigation: 'Sanitize all inputs and enforce strict schema validation'
      });
    }

    // Publish the red‑team result (could be empty array)
    this.bus.publish({
      id: `redteam-${event.id}`,
      type: 'verify.redteam',
      ts: Date.now(),
      source: 'RedTeamAgent',
      payload: {
        proposalId: event.id,
        vulnerabilities
      }
    });
  }
}
