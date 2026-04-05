import { Rule, Condition, Action } from './RuleParser';

export class RuleEngine {
  private rules: Rule[];
  constructor(rules: Rule[]) {
    this.rules = rules;
  }

  private evalCond(context: Record<string, unknown>, cond: Condition): boolean {
    const lhs = context[cond.field];
    const rhs = cond.value;
    switch (cond.op) {
      case '==': return lhs === rhs;
      case '!=': return lhs !== rhs;
      case '>': return (lhs as number) > (rhs as number);
      case '>=': return (lhs as number) >= (rhs as number);
      case '<': return (lhs as number) < (rhs as number);
      case '<=': return (lhs as number) <= (rhs as number);
      case 'in': return Array.isArray(rhs) && (rhs as any[]).includes(lhs);
      case 'contains': return typeof lhs === 'string' && typeof rhs === 'string' && lhs.includes(rhs);
      default: return false;
    }
  }

  evaluate(context: Record<string, unknown>): Action[] {
    const actions: Action[] = [];
    for (const rule of this.rules) {
      if (rule.when.every(c => this.evalCond(context, c))) {
        actions.push(...rule.then);
      }
    }
    return actions;
  }
}
