import { RuleParser } from '../../../rule-fabric/src/rules/engine/RuleParser';
import { RuleEngine } from '../../../rule-fabric/src/rules/engine/RuleEngine';

describe('RuleEngine', () => {
  const rules = RuleParser.load('global.yaml');
  const engine = new RuleEngine(rules);

  test('passes confidence threshold and low risk', () => {
    const context = {
      confidence: 0.9,
      riskScore: 'LOW',
      laneL: true,
      laneR: true,
    } as any;
    const actions = engine.evaluate(context);
    // Expect only a continue action (type "continue")
    const types = actions.map(a => a.type);
    expect(types).toContain('continue');
    expect(types).not.toContain('reject');
  });

  test('high risk triggers reject', () => {
    const context = {
      confidence: 0.9,
      riskScore: 'HIGH',
      laneL: true,
      laneR: true,
    } as any;
    const actions = engine.evaluate(context);
    const types = actions.map(a => a.type);
    expect(types).toContain('reject');
  });
});
