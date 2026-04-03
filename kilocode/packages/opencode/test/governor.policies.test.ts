import {
  loadPolicies,
  validateWithPolicies,
  validateOperationWithPolicies,
  validateOperation,
  loadProjectContext,
  PolicyCheck,
  PoliciesConfig,
} from '../src/kilocode/tools/governor';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('Policy validation', () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = path.join(__dirname, `tmp-policies-${Date.now()}`);
    await fs.mkdir(tempDir, { recursive: true });
  });

  afterEach(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  describe('loadPolicies', () => {
    test('returns null when policies.json does not exist', async () => {
      const result = await loadPolicies(tempDir);
      expect(result).toBeNull();
    });

    test('loads policies from .kilo/policies.json', async () => {
      const kiloDir = path.join(tempDir, '.kilo');
      await fs.mkdir(kiloDir, { recursive: true });

      const policiesConfig = {
        version: '1.0',
        policies: [
          {
            id: 'POL-001',
            name: 'Test Policy',
            type: 'require_role' as const,
            match: 'azure/storage/',
            details: { role: 'Storage Blob Data Contributor' },
            enabled: true,
          },
        ],
      };

      await fs.writeFile(
        path.join(kiloDir, 'policies.json'),
        JSON.stringify(policiesConfig)
      );

      const result = await loadPolicies(tempDir);
      expect(result).not.toBeNull();
      expect(result?.version).toBe('1.0');
      expect(result?.policies).toHaveLength(1);
      expect(result?.policies[0].name).toBe('Test Policy');
    });
  });

  describe('validateWithPolicies', () => {
    const samplePolicies: PoliciesConfig = {
      version: '1.0',
      policies: [
        {
          id: 'POL-001',
          name: 'Require Managed Identity for Storage',
          type: 'require_managed_identity',
          match: 'azure/storage/',
          details: { resourceType: 'Azure Storage Account' },
          enabled: true,
        },
        {
          id: 'POL-002',
          name: 'Require Role for Blob Writes',
          type: 'require_role',
          match: 'azure/blob/write',
          details: { role: 'Storage Blob Data Contributor' },
          enabled: true,
        },
        {
          id: 'POL-003',
          name: 'Block Key Rotation Without Approval',
          type: 'require_approval',
          match: 'azure/keyvault/rotate',
          details: { operation: 'Secret/Key rotation' },
          enabled: true,
        },
        {
          id: 'POL-004',
          name: 'Block Unauthenticated Azure Ops',
          type: 'block_unauthenticated',
          match: 'azure/',
          enabled: true,
        },
      ],
    };

    test('returns passing checks for non-matching operations', () => {
      const results = validateWithPolicies(samplePolicies, 'api/health/check');
      expect(results).toHaveLength(4);
      results.forEach((check) => {
        expect(check.passed).toBe(true);
      });
    });

    test('fails managed identity check for storage operations', () => {
      const results = validateWithPolicies(samplePolicies, 'azure/storage/delete');
      const managedIdentityCheck = results.find(
        (c) => c.policyName === 'Require Managed Identity for Storage'
      );
      expect(managedIdentityCheck).toBeDefined();
      expect(managedIdentityCheck?.passed).toBe(false);
      expect(managedIdentityCheck?.severity).toBe('critical');
      expect(managedIdentityCheck?.reason).toContain('managed identity');
    });

    test('fails role check for blob write operations', () => {
      const results = validateWithPolicies(samplePolicies, 'azure/blob/write/container');
      const roleCheck = results.find(
        (c) => c.policyName === 'Require Role for Blob Writes'
      );
      expect(roleCheck).toBeDefined();
      expect(roleCheck?.passed).toBe(false);
      expect(roleCheck?.severity).toBe('high');
      expect(roleCheck?.reason).toContain('Storage Blob Data Contributor');
    });

    test('fails approval check for key rotation', () => {
      const results = validateWithPolicies(samplePolicies, 'azure/keyvault/rotate/secret1');
      const approvalCheck = results.find(
        (c) => c.policyName === 'Block Key Rotation Without Approval'
      );
      expect(approvalCheck).toBeDefined();
      expect(approvalCheck?.passed).toBe(false);
      expect(approvalCheck?.severity).toBe('high');
      expect(approvalCheck?.reason).toContain('requires explicit approval');
    });

    test('fails unauthenticated check for any azure operation', () => {
      const results = validateWithPolicies(samplePolicies, 'azure/vm/start');
      const unauthCheck = results.find(
        (c) => c.policyName === 'Block Unauthenticated Azure Ops'
      );
      expect(unauthCheck).toBeDefined();
      expect(unauthCheck?.passed).toBe(false);
      expect(unauthCheck?.severity).toBe('critical');
      expect(unauthCheck?.reason).toContain('Azure AD authentication');
    });

    test('skips disabled policies', () => {
      const policiesWithDisabled: PoliciesConfig = {
        version: '1.0',
        policies: [
          {
            name: 'Disabled Policy',
            type: 'require_role',
            match: 'azure/',
            details: { role: 'Owner' },
            enabled: false,
          },
        ],
      };

      const results = validateWithPolicies(policiesWithDisabled, 'azure/storage/delete');
      expect(results).toHaveLength(0);
    });

    test('handles unknown policy type gracefully', () => {
      const policiesWithUnknown: PoliciesConfig = {
        version: '1.0',
        policies: [
          {
            name: 'Unknown Type Policy',
            type: 'unknown_type' as any,
            match: 'azure/',
            enabled: true,
          },
        ],
      };

      const results = validateWithPolicies(policiesWithUnknown, 'azure/test');
      expect(results).toHaveLength(1);
      expect(results[0].passed).toBe(true);
      expect(results[0].reason).toContain('Unknown policy type');
    });
  });

  describe('validateOperationWithPolicies', () => {
    test('returns danger zone result when no policies file exists', async () => {
      const manifest = {
        name: 'TestProject',
        lifecycle: 'production',
        dangerZones: ['api/secure/'],
      };
      await fs.writeFile(
        path.join(tempDir, 'project.manifest.json'),
        JSON.stringify(manifest)
      );

      const context = await loadProjectContext(tempDir);
      const result = await validateOperationWithPolicies(context, 'api/users/list', tempDir);

      expect(result.allowed).toBe(true);
      expect(result.policies).toBeUndefined();
    });

    test('combines danger zone and policy checks when both exist', async () => {
      const kiloDir = path.join(tempDir, '.kilo');
      await fs.mkdir(kiloDir, { recursive: true });

      const manifest = {
        name: 'TestProject',
        lifecycle: 'production',
        dangerZones: ['api/secure/'],
      };
      await fs.writeFile(
        path.join(tempDir, 'project.manifest.json'),
        JSON.stringify(manifest)
      );

      const policiesConfig: PoliciesConfig = {
        version: '1.0',
        policies: [
          {
            name: 'Require Managed Identity',
            type: 'require_managed_identity',
            match: 'azure/storage/',
            details: { resourceType: 'Storage Account' },
            enabled: true,
          },
        ],
      };
      await fs.writeFile(
        path.join(kiloDir, 'policies.json'),
        JSON.stringify(policiesConfig)
      );

      // Safe operation — passes both checks
      const safeResult = await validateOperationWithPolicies(
        { name: 'TestProject', lifecycle: 'production', dangerZones: [] },
        'api/users/list',
        tempDir
      );
      expect(safeResult.allowed).toBe(true);
      expect(safeResult.policies).toHaveLength(1);
      expect(safeResult.policies?.[0].passed).toBe(true);

      // Policy violation — fails policy check
      const policyFailResult = await validateOperationWithPolicies(
        { name: 'TestProject', lifecycle: 'production', dangerZones: [] },
        'azure/storage/delete',
        tempDir
      );
      expect(policyFailResult.allowed).toBe(false);
      expect(policyFailResult.policies).toHaveLength(1);
      expect(policyFailResult.policies?.[0].passed).toBe(false);
      expect(policyFailResult.reason).toContain('managed identity');

      // Danger zone violation — fails danger zone check
      const dangerFailResult = await validateOperationWithPolicies(
        { name: 'TestProject', lifecycle: 'production', dangerZones: ['api/secure/'] },
        'api/secure/keys',
        tempDir
      );
      expect(dangerFailResult.allowed).toBe(false);
      expect(dangerFailResult.reason).toContain('danger zone');
    });

    test('returns most severe failed policy in reason', async () => {
      const kiloDir = path.join(tempDir, '.kilo');
      await fs.mkdir(kiloDir, { recursive: true });

      const policiesConfig: PoliciesConfig = {
        version: '1.0',
        policies: [
          {
            name: 'Critical Policy',
            type: 'require_managed_identity',
            match: 'azure/storage/',
            details: { resourceType: 'Storage Account' },
            enabled: true,
          },
          {
            name: 'High Policy',
            type: 'require_role',
            match: 'azure/storage/',
            details: { role: 'Owner' },
            enabled: true,
          },
        ],
      };
      await fs.writeFile(
        path.join(kiloDir, 'policies.json'),
        JSON.stringify(policiesConfig)
      );

      const result = await validateOperationWithPolicies(
        { name: 'TestProject', lifecycle: 'production' },
        'azure/storage/delete',
        tempDir
      );

      expect(result.allowed).toBe(false);
      expect(result.policies).toHaveLength(2);
      expect(result.reason).toContain('managed identity');
    });

    test('produces TTS narration for policy failures', async () => {
      const kiloDir = path.join(tempDir, '.kilo');
      await fs.mkdir(kiloDir, { recursive: true });

      const policiesConfig: PoliciesConfig = {
        version: '1.0',
        policies: [
          {
            name: 'Single Policy',
            type: 'require_role',
            match: 'azure/blob/write',
            details: { role: 'Contributor' },
            enabled: true,
          },
        ],
      };
      await fs.writeFile(
        path.join(kiloDir, 'policies.json'),
        JSON.stringify(policiesConfig)
      );

      const result = await validateOperationWithPolicies(
        { name: 'TestProject', lifecycle: 'production' },
        'azure/blob/write/container',
        tempDir
      );

      expect(result.ttsNarration).toBeDefined();
      expect(result.ttsNarration).toContain('blocked by 1 policy check');
    });

    test('uses process.cwd() when projectRoot is not provided', async () => {
      const result = await validateOperationWithPolicies(
        { name: 'TestProject', lifecycle: 'production' },
        'api/health/check'
      );

      expect(result.allowed).toBe(true);
    });
  });

  describe('PolicyCheck interface structure', () => {
    test('PolicyCheck has all required fields', () => {
      const check: PolicyCheck = {
        policyName: 'Test Policy',
        passed: false,
        reason: 'Test reason',
        severity: 'high',
      };

      expect(check.policyName).toBe('Test Policy');
      expect(check.passed).toBe(false);
      expect(check.reason).toBe('Test reason');
      expect(check.severity).toBe('high');
    });

    test('severity accepts all valid values', () => {
      const severities: Array<'critical' | 'high' | 'medium' | 'low'> = [
        'critical',
        'high',
        'medium',
        'low',
      ];

      severities.forEach((severity) => {
        const check: PolicyCheck = {
          policyName: 'Test',
          passed: true,
          reason: 'Test',
          severity,
        };
        expect(check.severity).toBe(severity);
      });
    });
  });
});
