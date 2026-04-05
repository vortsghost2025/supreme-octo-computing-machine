import { Action } from './RuleParser';
import { BaseAdapter } from '../../adapters/BaseAdapter.js';
import { N8nAdapter } from '../../adapters/n8n/N8nAdapter.js';
import { EsAdapter } from '../../adapters/es/EsAdapter.js';

export class RuleExecutor {
  private adapters: Record<string, BaseAdapter>;

  constructor() {
    this.adapters = {
      n8n: new N8nAdapter(),
      es: new EsAdapter(),
    };
  }

  async execute(actions: Action[], context: Record<string, unknown>) {
    for (const a of actions) {
      switch (a.type) {
        case 'reject':
          throw new Error('Proposal rejected by rule');
        case 'escalate':
          // escalate event published later by orchestrator
          break;
        case 'runAdapter':
          const target = a.params?.target as string;
          const method = a.params?.method as keyof BaseAdapter;
          const args = a.params?.args as any[];
          if (!this.adapters[target]) throw new Error(`Adapter ${target} missing`);
          const result = await (this.adapters[target][method] as any)(...args);
          context[`adapterResult_${target}`] = result;
          break;
        // add more actions as needed
      }
    }
  }
}
