import {
  loadProjectContext,
  validateOperation,
  searchLibrary,
  getCrossProjectGuidance,
  generateNarration,
  refreshContext,
} from '../src/kilocode/tools/governor';
import {
  registerGovernor,
  getRegistration,
  unregisterGovernor,
  governorTools,
} from '../src/kilocode/register';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('Governor Integration Tests', () => {
  let tempDir: string;

  beforeEach(async () => {
    tempDir = path.join(__dirname, `tmp-integration-${Date.now()}`);
    await fs.mkdir(tempDir, { recursive: true });
  });

  afterEach(async () => {
    await unregisterGovernor();
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  describe('Full tool registration flow', () => {
    test('register, verify all 6 tools are callable, unregister', async () => {
      const manifest = {
        name: 'IntegrationTestProject',
        lifecycle: 'development',
        dangerZones: ['api/secure/'],
        allowedImports: ['lodash', 'express'],
      };
      await fs.writeFile(
        path.join(tempDir, 'project.manifest.json'),
        JSON.stringify(manifest)
      );

      const registration = await registerGovernor(tempDir);
      expect(registration).toBeDefined();
      expect(registration.tools).toHaveLength(6);

      const toolNames = registration.tools.map((t) => t.name);
      expect(toolNames).toContain('governor_load_context');
      expect(toolNames).toContain('governor_validate');
      expect(toolNames).toContain('governor_search');
      expect(toolNames).toContain('governor_guidance');
      expect(toolNames).toContain('governor_narrate');
      expect(toolNames).toContain('governor_refresh');

      for (const tool of registration.tools) {
        expect(typeof tool.handler).toBe('function');
      }

      const reg = getRegistration();
      expect(reg).not.toBeNull();
      expect(reg?.context?.name).toBe('IntegrationTestProject');

      await unregisterGovernor();
      expect(getRegistration()).toBeNull();
    });
  });

  describe('searchLibrary with real index.json', () => {
    test('returns matching entries from .kilo/library/index.json', async () => {
      const libraryDir = path.join(tempDir, '.kilo', 'library');
      await fs.mkdir(libraryDir, { recursive: true });

      const libraryData = [
        {
          id: 'auth-001',
          title: 'OAuth2 Authentication Flow',
          snippet: 'Standard OAuth2 PKCE flow for web applications',
          tags: ['auth', 'oauth', 'security'],
          relevance: 0.95,
        },
        {
          id: 'cache-001',
          title: 'Redis Cache Manager',
          snippet: 'Connection pooling and TTL management for Redis',
          tags: ['cache', 'redis', 'performance'],
          relevance: 0.87,
        },
        {
          id: 'api-001',
          title: 'REST API Error Handler',
          snippet: 'Centralized error handling with HTTP status codes',
          tags: ['api', 'error', 'rest'],
          relevance: 0.92,
        },
      ];

      await fs.writeFile(
        path.join(libraryDir, 'index.json'),
        JSON.stringify(libraryData)
      );

      const originalCwd = process.cwd();
      process.chdir(tempDir);

      try {
        const results = await searchLibrary('auth');
        expect(results).toHaveLength(1);
        expect(results[0].id).toBe('auth-001');

        const cacheResults = await searchLibrary('cache');
        expect(cacheResults).toHaveLength(1);
        expect(cacheResults[0].title).toBe('Redis Cache Manager');

        const noResults = await searchLibrary('nonexistent');
        expect(noResults).toHaveLength(0);
      } finally {
        process.chdir(originalCwd);
      }
    });

    test('returns empty array when library index does not exist', async () => {
      const originalCwd = process.cwd();
      process.chdir(tempDir);

      try {
        const results = await searchLibrary('anything');
        expect(results).toEqual([]);
      } finally {
        process.chdir(originalCwd);
      }
    });
  });

  describe('getCrossProjectGuidance with real registry.json', () => {
    test('returns guidance for known project from .kilo/registry.json', async () => {
      const kiloDir = path.join(tempDir, '.kilo');
      await fs.mkdir(kiloDir, { recursive: true });

      const registryData = {
        paymentService: {
          projectName: 'paymentService',
          lifecycle: 'production',
          dangerZones: ['src/billing/', 'src/refunds/'],
          notes: ['PCI compliance required', 'All changes need security review'],
        },
        userService: {
          projectName: 'userService',
          lifecycle: 'development',
          dangerZones: ['src/auth/'],
          notes: ['GDPR data handling in user model'],
        },
      };

      await fs.writeFile(
        path.join(kiloDir, 'registry.json'),
        JSON.stringify(registryData)
      );

      const originalCwd = process.cwd();
      process.chdir(tempDir);

      try {
        const guidance = await getCrossProjectGuidance('paymentService');
        expect(guidance.projectName).toBe('paymentService');
        expect(guidance.lifecycle).toBe('production');
        expect(guidance.dangerZones).toContain('src/billing/');
        expect(guidance.notes).toContain('PCI compliance required');

        const unknownGuidance = await getCrossProjectGuidance('unknownService');
        expect(unknownGuidance.projectName).toBe('unknownService');
        expect(unknownGuidance.lifecycle).toBe('unknown');
        expect(unknownGuidance.notes).toContain('No guidance found for this project.');
      } finally {
        process.chdir(originalCwd);
      }
    });

    test('returns fallback when registry file does not exist', async () => {
      const originalCwd = process.cwd();
      process.chdir(tempDir);

      try {
        const guidance = await getCrossProjectGuidance('anyProject');
        expect(guidance.projectName).toBe('anyProject');
        expect(guidance.lifecycle).toBe('unknown');
        expect(guidance.dangerZones).toEqual([]);
        expect(guidance.notes[0]).toContain('Project registry not found');
      } finally {
        process.chdir(originalCwd);
      }
    });
  });

  describe('generateNarration produces valid SSML', () => {
    test('wraps message in SSML speak element', () => {
      const ssml = generateNarration('Hello world');
      expect(ssml).toContain('<speak');
      expect(ssml).toContain('version="1.0"');
      expect(ssml).toContain('xmlns="http://www.w3.org/2001/10/synthesis"');
      expect(ssml).toContain('xml:lang="en-US"');
      expect(ssml).toContain('<voice name="en-US-AriaNeural">');
      expect(ssml).toContain('<prosody rate="medium" pitch="default">');
      expect(ssml).toContain('Hello world');
      expect(ssml).toContain('</speak>');
    });

    test('escapes special XML characters', () => {
      const ssml = generateNarration('Test & "quotes" <tags>');
      expect(ssml).toContain('Test &amp; &quot;quotes&quot; &lt;tags&gt;');
      expect(ssml).not.toContain('Test & "');
    });

    test('handles apostrophes correctly', () => {
      const ssml = generateNarration("It's working");
      expect(ssml).toContain("&apos;");
    });
  });

  describe('refreshContext re-reads manifest and clears caches', () => {
    test('reloads updated manifest and clears library cache', async () => {
      const manifest = {
        name: 'InitialProject',
        lifecycle: 'development',
        dangerZones: ['api/v1/'],
      };
      await fs.writeFile(
        path.join(tempDir, 'project.manifest.json'),
        JSON.stringify(manifest)
      );

      let context = await loadProjectContext(tempDir);
      expect(context.name).toBe('InitialProject');
      expect(context.lifecycle).toBe('development');

      const updatedManifest = {
        name: 'UpdatedProject',
        lifecycle: 'production',
        dangerZones: ['api/v2/', 'admin/'],
      };
      await fs.writeFile(
        path.join(tempDir, 'project.manifest.json'),
        JSON.stringify(updatedManifest)
      );

      context = await refreshContext(tempDir);
      expect(context.name).toBe('UpdatedProject');
      expect(context.lifecycle).toBe('production');
      expect(context.dangerZones).toContain('admin/');
    });
  });

  describe('End-to-end: register → load → validate → search → narrate → unregister', () => {
    test('full governor workflow', async () => {
      const manifest = {
        name: 'E2EProject',
        lifecycle: 'production',
        dangerZones: ['api/payments/', 'admin/'],
        allowedImports: ['express', 'lodash'],
      };
      await fs.writeFile(
        path.join(tempDir, 'project.manifest.json'),
        JSON.stringify(manifest)
      );

      const libraryDir = path.join(tempDir, '.kilo', 'library');
      await fs.mkdir(libraryDir, { recursive: true });
      const libraryData = [
        {
          id: 'e2e-001',
          title: 'Payment Validation Helper',
          snippet: 'Validates payment amounts and currency codes',
          tags: ['payment', 'validation', 'e2e'],
          relevance: 0.99,
        },
      ];
      await fs.writeFile(
        path.join(libraryDir, 'index.json'),
        JSON.stringify(libraryData)
      );

      const kiloDir = path.join(tempDir, '.kilo');
      const registryData = {
        E2EProject: {
          projectName: 'E2EProject',
          lifecycle: 'production',
          dangerZones: ['api/payments/', 'admin/'],
          notes: ['End-to-end test project'],
        },
      };
      await fs.writeFile(
        path.join(kiloDir, 'registry.json'),
        JSON.stringify(registryData)
      );

      const originalCwd = process.cwd();
      process.chdir(tempDir);

      try {
        const registration = await registerGovernor(tempDir);
        expect(registration.context?.name).toBe('E2EProject');

        const context = await loadProjectContext(tempDir);
        expect(context.name).toBe('E2EProject');
        expect(context.lifecycle).toBe('production');

        const safeResult = validateOperation(context, 'api/users/list');
        expect(safeResult.allowed).toBe(true);

        const dangerResult = validateOperation(context, 'api/payments/process');
        expect(dangerResult.allowed).toBe(false);
        expect(dangerResult.ttsNarration).toBeDefined();

        const searchResults = await searchLibrary('payment');
        expect(searchResults).toHaveLength(1);
        expect(searchResults[0].id).toBe('e2e-001');

        const narration = generateNarration('Operation completed successfully');
        expect(narration).toContain('<speak');
        expect(narration).toContain('Operation completed successfully');

        const refreshed = await refreshContext(tempDir);
        expect(refreshed.name).toBe('E2EProject');

        await unregisterGovernor();
        expect(getRegistration()).toBeNull();
      } finally {
        process.chdir(originalCwd);
      }
    });
  });
});
