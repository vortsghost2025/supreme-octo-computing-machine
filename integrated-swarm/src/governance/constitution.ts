import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import Jexl from 'jexl';

/**
 * Types representing the constitution DSL.
 */
export interface Invariant {
  id: string;
  severity: string;
  rule: string; // JEXL expression
}

export interface Policy {
  id: string;
  rule: string; // JEXL expression
}

export interface Constitution {
  version: string;
  invariants: Invariant[];
  policies: Policy[];
}

/**
 * Load the constitution YAML file from the project root.
 */
export function loadConstitution(): Constitution {
  const constitutionPath = path.resolve(
    process.cwd(),
    'integrated-swarm',
    'src',
    'governance',
    'constitution.yaml'
  );
  const raw = fs.readFileSync(constitutionPath, 'utf8');
  const data = yaml.load(raw) as Constitution;
  return data;
}

/**
 * Evaluate a single JEXL rule against a context.
 * Returns true if the rule evaluates to a truthy value.
 */
export async function evaluateRule(rule: string, context: Record<string, any>): Promise<boolean> {
  try {
    const result = await Jexl.eval(rule, context);
    return Boolean(result);
  } catch (e) {
    console.error('Rule evaluation error:', rule, e);
    return false;
  }
}

/**
 * Verify that a proposal satisfies all invariants and policies.
 * Returns an object describing any violations.
 */
export async function verifyConstitution(context: Record<string, any>) {
  const constitution = loadConstitution();
  const invariantViolations: string[] = [];
  for (const inv of constitution.invariants) {
    const ok = await evaluateRule(inv.rule, context);
    if (!ok) invariantViolations.push(inv.id);
  }
  const policyViolations: string[] = [];
  for (const pol of constitution.policies) {
    const ok = await evaluateRule(pol.rule, context);
    if (!ok) policyViolations.push(pol.id);
  }
  return {
    satisfied: invariantViolations.length === 0 && policyViolations.length === 0,
    invariantViolations,
    policyViolations,
  };
}
