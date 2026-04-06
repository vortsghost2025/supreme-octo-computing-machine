import { handleProposal } from './agentMessagePasser.js';
async function run() {
    console.log('--- Test 1: Passing proposal (confidence 92, MEDIUM risk) ---');
    const pass = await handleProposal({
        id: 'test-workflow-1',
        changes: JSON.stringify({ nodes: [], connections: {} }),
        confidence: 92,
    });
    console.log('Result:', pass);
    console.log('\n--- Test 2: Failing proposal (confidence 70, MEDIUM risk) ---');
    const fail = await handleProposal({
        id: 'test-workflow-2',
        changes: JSON.stringify({ nodes: [], connections: {} }),
        confidence: 70,
    });
    console.log('Result:', fail);
}
run().catch(e => console.error('Unexpected error', e));
