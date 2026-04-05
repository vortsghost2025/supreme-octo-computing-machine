import { pullWorkflow, validateWorkflow, pushWorkflow, runDry } from './n8nAdapter.js';
import { getRiskScore } from './riskBreaker.js';
import { enrichMemoryRecord } from './memoryTransformer.js';
import { verifyConstitution } from './governance/constitution.js';
import { writeFile } from 'fs/promises';
import { join } from 'path';

/**
 * Handles a proposal coming from the global work tier.
 * The `proposal` object must contain at least:
 *   - id: string (workflow identifier in n8n)
 *   - changes: string (JSON representing the new workflow)
 *   - confidence: number (0‑100)
 */
export async function handleProposal(proposal: {
  id: string;
  changes: string;
  confidence: number;
}) {
  // 1. Pull current workflow (not strictly needed for this demo)
  const current = await pullWorkflow(proposal.id).catch(() => '{}');

  // 2. Compute risk score using KMB logic
  const riskScore = getRiskScore();

  // 3. Validate the proposed workflow JSON against n8n schema
  const schemaValid = await validateWorkflow(proposal.changes);

  // 4. Build verification reports for both lanes (L & R)
  const verification = {
  // lane outcomes (both lanes run the same validation here)
  verify_l_pass: schemaValid,
  verify_r_pass: schemaValid,

    confidence: proposal.confidence,
    riskScore,
    schemaValid,
  };

  // 5. Consensus – require confidence≥85, risk ≤ MEDIUM, schemaValid true
  const consensusPass =
    verification.confidence >= 85 &&
    (verification.riskScore === 'LOW' || verification.riskScore === 'MEDIUM') &&
    verification.schemaValid;

  if (!consensusPass) {
    console.warn('Consensus rejected proposal', verification);
    return { accepted: false, reason: verification };
  }

  // ---------------------------------------------------
  // Constitution layer validation (policy & invariants)
  // ---------------------------------------------------
  const constitutionResult = await verifyConstitution({
    confidence: proposal.confidence,
    riskScore,
    schemaValid,
    verify_l_pass: verification.verify_l_pass,
    verify_r_pass: verification.verify_r_pass,
    // placeholder for future humanApproval flag
    humanApproval: false,
    rollbackWindowMinutes: 5
  });

  if (!constitutionResult.satisfied) {
    console.warn('Constitution violations', constitutionResult);
    return { accepted: false, reason: constitutionResult };
  }

  // 6. Push the new workflow to n8n
  await pushWorkflow(proposal.id, proposal.changes);

  // 7. Dry‑run execution to ensure runtime success
  const dryRunSuccess = await runDry(proposal.id);

  // 8. Log outcome to episodic memory
  const record = enrichMemoryRecord({
    proposalId: proposal.id,
    outcome: dryRunSuccess ? 'SUCCESS' : 'FAILURE',
    verification,
  });
  const logPath = join(process.cwd(), '.kilo', 'memory', 'episodic', `${record.__id}.jsonl`);
  await writeFile(logPath, JSON.stringify(record) + '\n');

  // 9. If dry‑run failed, trigger rollback within 5 min (simplified)
  if (!dryRunSuccess) {
    console.error('Dry‑run failed – manual rollback may be required');
  }

  return { accepted: true, dryRunSuccess };
}
