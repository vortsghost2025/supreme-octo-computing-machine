import { N8nAdapter } from '../../adapters/n8n/N8nAdapter';
import { EsAdapter } from '../../adapters/es/EsAdapter';
export class RuleExecutor {
    adapters;
    constructor() {
        this.adapters = {
            n8n: new N8nAdapter(),
            es: new EsAdapter(),
        };
    }
    async execute(actions, context) {
        for (const a of actions) {
            switch (a.type) {
                case 'reject':
                    throw new Error('Proposal rejected by rule');
                case 'escalate':
                    // escalate event published later by orchestrator
                    break;
                case 'runAdapter':
                    const target = a.params?.target;
                    const method = a.params?.method;
                    const args = a.params?.args;
                    if (!this.adapters[target])
                        throw new Error(`Adapter ${target} missing`);
                    const result = await this.adapters[target][method](...args);
                    context[`adapterResult_${target}`] = result;
                    break;
                // add more actions as needed
            }
        }
    }
}
