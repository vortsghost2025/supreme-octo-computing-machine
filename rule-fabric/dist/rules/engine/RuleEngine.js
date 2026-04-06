export class RuleEngine {
    rules;
    constructor(rules) {
        this.rules = rules;
    }
    evalCond(context, cond) {
        const lhs = context[cond.field];
        const rhs = cond.value;
        switch (cond.op) {
            case '==': return lhs === rhs;
            case '!=': return lhs !== rhs;
            case '>': return lhs > rhs;
            case '>=': return lhs >= rhs;
            case '<': return lhs < rhs;
            case '<=': return lhs <= rhs;
            case 'in': return Array.isArray(rhs) && rhs.includes(lhs);
            case 'contains': return typeof lhs === 'string' && typeof rhs === 'string' && lhs.includes(rhs);
            default: return false;
        }
    }
    evaluate(context) {
        const actions = [];
        for (const rule of this.rules) {
            if (rule.when.every(c => this.evalCond(context, c))) {
                actions.push(...rule.then);
            }
        }
        return actions;
    }
}
