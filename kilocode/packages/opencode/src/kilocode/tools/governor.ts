import * as fs from 'fs/promises';
import * as path from 'path';

export interface ProjectContext {
  name: string;
  lifecycle: string;
  dangerZones?: string[]; // paths that are considered dangerous
  allowedImports?: string[];
  [key: string]: any;
}

export interface ValidationResult {
  allowed: boolean;
  reason?: string;
  ttsNarration?: string;
  policies?: PolicyCheck[];
}

export interface PolicyCheck {
  policyName: string;
  passed: boolean;
  reason: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

export interface PolicyRule {
  id?: string;
  name: string;
  type: 'require_role' | 'require_managed_identity' | 'block_unauthenticated' | 'require_approval';
  match: string; // path pattern to match
  details?: {
    role?: string;
    resourceType?: string;
    operation?: string;
  };
  enabled?: boolean;
}

export interface PoliciesConfig {
  version?: string;
  policies: PolicyRule[];
}

/**
 * Load policies from .kilo/policies.json if present.
 * Returns null if the file doesn't exist.
 */
export async function loadPolicies(projectRoot?: string): Promise<PoliciesConfig | null> {
  const policiesPath = path.join(projectRoot ?? process.cwd(), '.kilo', 'policies.json');
  try {
    const raw = await fs.readFile(policiesPath, { encoding: 'utf-8' });
    return JSON.parse(raw) as PoliciesConfig;
  } catch {
    return null;
  }
}

/**
 * Evaluate a single policy rule against an operation path.
 * Simulated — no real Azure SDK calls are made, but the structure
 * is designed so real checks can be dropped in later.
 */
function evaluatePolicyRule(rule: PolicyRule, operationPath: string): PolicyCheck {
  const normalized = operationPath.replace(/^\//, '');
  const normalizedMatch = rule.match.replace(/^\//, '');

  const matches = normalized.startsWith(normalizedMatch) || normalized.includes(normalizedMatch);

  if (!matches) {
    return {
      policyName: rule.name,
      passed: true,
      reason: `Operation does not match policy scope "${rule.match}"`,
      severity: 'low',
    };
  }

  switch (rule.type) {
    case 'require_role': {
      const requiredRole = rule.details?.role ?? 'unspecified';
      return {
        policyName: rule.name,
        passed: false, // simulated: assume role not granted
        reason: `Operation matches "${rule.match}" and requires Azure RBAC role "${requiredRole}". Simulated check: role not verified.`,
        severity: 'high',
      };
    }
    case 'require_managed_identity': {
      const resourceType = rule.details?.resourceType ?? 'resource';
      return {
        policyName: rule.name,
        passed: false, // simulated: assume no managed identity
        reason: `Operation on ${resourceType} at "${rule.match}" requires a managed identity. Simulated check: no managed identity detected.`,
        severity: 'critical',
      };
    }
    case 'block_unauthenticated': {
      return {
        policyName: rule.name,
        passed: false, // simulated: assume unauthenticated
        reason: `Operation "${operationPath}" is blocked because it does not use Azure AD authentication. Simulated check: no auth context found.`,
        severity: 'critical',
      };
    }
    case 'require_approval': {
      const operation = rule.details?.operation ?? 'operation';
      return {
        policyName: rule.name,
        passed: false, // simulated: assume no approval
        reason: `${operation} at "${rule.match}" requires explicit approval. Simulated check: no approval token found.`,
        severity: 'high',
      };
    }
    default: {
      return {
        policyName: rule.name,
        passed: true,
        reason: `Unknown policy type "${(rule as PolicyRule).type}", skipping evaluation.`,
        severity: 'low',
      };
    }
  }
}

/**
 * Run policy checks against an operation path.
 * Returns a list of PolicyCheck results for all enabled policies.
 */
export function validateWithPolicies(
  policies: PoliciesConfig,
  operationPath: string
): PolicyCheck[] {
  return policies.policies
    .filter((rule) => rule.enabled !== false)
    .map((rule) => evaluatePolicyRule(rule, operationPath));
}

/**
 * Validate an operation path against both danger zones AND policy rules.
 * Reads .kilo/policies.json if present and runs policy checks in addition
 * to the existing danger zone prefix matching.
 */
export async function validateOperationWithPolicies(
  context: ProjectContext,
  operationPath: string,
  projectRoot?: string
): Promise<ValidationResult> {
  const dangerZoneResult = validateOperation(context, operationPath);

  const policies = await loadPolicies(projectRoot);
  if (!policies) {
    return dangerZoneResult;
  }

  const policyChecks = validateWithPolicies(policies, operationPath);
  const failedPolicies = policyChecks.filter((check) => !check.passed);
  const mostSevere = failedPolicies.length > 0
    ? failedPolicies.reduce((a, b) => {
        const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        return severityOrder[a.severity] <= severityOrder[b.severity] ? a : b;
      })
    : null;

  const overallAllowed = dangerZoneResult.allowed && failedPolicies.length === 0;
  const reasons: string[] = [];
  if (!dangerZoneResult.allowed && dangerZoneResult.reason) {
    reasons.push(dangerZoneResult.reason);
  }
  if (mostSevere) {
    reasons.push(mostSevere.reason);
  }

  return {
    allowed: overallAllowed,
    reason: reasons.join(' ') || undefined,
    ttsNarration: overallAllowed
      ? undefined
      : `Access denied. The operation is blocked by ${failedPolicies.length} policy check${failedPolicies.length === 1 ? '' : 's'}.`,
    policies: policyChecks,
  };
}

/**
 * Load a project's context by reading its manifest file.
 * Expected file: <projectRoot>/project.manifest.json
 */
export async function loadProjectContext(projectRoot: string): Promise<ProjectContext> {
  const manifestPath = `${projectRoot.replace(/\/+$/, '')}/project.manifest.json`;
  try {
    const raw = await fs.readFile(manifestPath, { encoding: 'utf-8' });
    const parsed = JSON.parse(raw);
    return {
      name: parsed.name ?? 'unknown',
      lifecycle: parsed.lifecycle ?? 'development',
      dangerZones: parsed.dangerZones ?? [],
      allowedImports: parsed.allowedImports ?? [],
      ...parsed,
    } as ProjectContext;
  } catch (err) {
    throw new Error(`Failed to load project manifest at ${manifestPath}: ${(err as Error).message}`);
  }
}

/**
 * Validate an operation path against a project's danger zones.
 * Returns a ValidationResult with a TTS‑friendly narration string.
 */
export function validateOperation(context: ProjectContext, operationPath: string): ValidationResult {
  const normalized = operationPath.replace(/^\//, '');
  const isDanger = (context.dangerZones ?? []).some((zone) => {
    // simple prefix match, can be enhanced with glob patterns later
    return normalized.startsWith(zone.replace(/^\//, ''));
  });

  if (isDanger) {
    const reason = `Operation ${operationPath} is blocked by danger zone configuration.`;
    const tts = `Access denied. The requested operation is considered unsafe for this project.`;
    return { allowed: false, reason, ttsNarration: tts };
  }

  return { allowed: true };
}

export interface LibraryEntry {
  id: string;
  title: string;
  snippet: string;
  tags: string[];
  relevance: number;
}

const _libraryCache: Map<string, LibraryEntry[]> = new Map();

/**
 * Search the Neural‑Graph library index.
 * Reads from .kilo/library/index.json if present, otherwise returns empty.
 */
export async function searchLibrary(query: string): Promise<LibraryEntry[]> {
  const cacheKey = query.toLowerCase();
  if (_libraryCache.has(cacheKey)) {
    return _libraryCache.get(cacheKey)!;
  }

  try {
    const raw = await fs.readFile('.kilo/library/index.json', { encoding: 'utf-8' });
    const index: LibraryEntry[] = JSON.parse(raw);
    const results = index.filter((entry) =>
      entry.title.toLowerCase().includes(cacheKey) ||
      entry.snippet.toLowerCase().includes(cacheKey) ||
      entry.tags.some((t) => t.toLowerCase().includes(cacheKey))
    );
    _libraryCache.set(cacheKey, results);
    return results;
  } catch {
    return [];
  }
}

export interface ProjectGuidance {
  projectName: string;
  lifecycle: string;
  dangerZones: string[];
  notes: string[];
}

/**
 * Get cross‑project guidance from .kilo/registry.json.
 */
export async function getCrossProjectGuidance(projectName: string): Promise<ProjectGuidance> {
  try {
    const raw = await fs.readFile('.kilo/registry.json', { encoding: 'utf-8' });
    const registry: Record<string, ProjectGuidance> = JSON.parse(raw);
    return registry[projectName] ?? {
      projectName,
      lifecycle: 'unknown',
      dangerZones: [],
      notes: ['No guidance found for this project.'],
    };
  } catch {
    return {
      projectName,
      lifecycle: 'unknown',
      dangerZones: [],
      notes: ['Project registry not found. Create .kilo/registry.json to enable cross-project guidance.'],
    };
  }
}

/**
 * Generate SSML‑wrapped narration for TTS.
 */
export function generateNarration(message: string): string {
  return `<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
  <voice name="en-US-AriaNeural">
    <prosody rate="medium" pitch="default">${escapeXml(message)}</prosody>
  </voice>
</speak>`;
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * Refresh cached project context by re-reading the manifest and clearing caches.
 */
export async function refreshContext(projectRoot: string): Promise<ProjectContext> {
  _libraryCache.clear();
  return loadProjectContext(projectRoot);
}

