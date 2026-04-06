import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import Jexl from 'jexl';
/**
 * Load the constitution YAML file from the project root.
 */
export function loadConstitution() {
    const constitutionPath = path.resolve(process.cwd(), 'integrated-swarm', 'src', 'governance', 'constitution.yaml');
    const raw = fs.readFileSync(constitutionPath, 'utf8');
    const data = yaml.load(raw);
    return data;
}
/**
 * Evaluate a single JEXL rule against a context.
 * Returns true if the rule evaluates to a truthy value.
 */
export async function evaluateRule(rule, context) {
    try {
        const result = await Jexl.eval(rule, context);
        return Boolean(result);
    }
    catch (e) {
        console.error('Rule evaluation error:', rule, e);
        return false;
    }
}
/**
 * Verify that a proposal satisfies all invariants and policies.
 * Returns an object describing any violations.
 */
export async function verifyConstitution(context) {
    const constitution = loadConstitution();
    const invariantViolations = [];
    for (const inv of constitution.invariants) {
        const ok = await evaluateRule(inv.rule, context);
        if (!ok)
            invariantViolations.push(inv.id);
    }
    const policyViolations = [];
    for (const pol of constitution.policies) {
        const ok = await evaluateRule(pol.rule, context);
        if (!ok)
            policyViolations.push(pol.id);
    }
    return {
        satisfied: invariantViolations.length === 0 && policyViolations.length === 0,
        invariantViolations,
        policyViolations,
    };
}
