import { RuleParser } from '../rules/engine/RuleParser.js';
import { RuleEngine } from '../rules/engine/RuleEngine.js';
import { RuleExecutor } from '../rules/engine/RuleExecutor.js';
import { EventBus } from '../bus/EventBus.js';
export class Constitution {
    engine;
    executor;
    bus = EventBus.get();
    constructor() {
        const rules = RuleParser.load('global.yaml');
        this.engine = new RuleEngine(rules);
        this.executor = new RuleExecutor();
    }
    async validate(event) {
        const actions = this.engine.evaluate(event.payload);
        await this.executor.execute(actions, event.payload);
        this.bus.publish({
            id: `constitution-${event.id}`,
            type: 'governance.constitution.applied',
            ts: Date.now(),
            source: 'Constitution',
            payload: { eventId: event.id, actions },
        });
    }
}
