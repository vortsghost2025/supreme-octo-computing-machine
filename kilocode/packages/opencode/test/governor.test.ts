import { loadProjectContext, validateOperation } from '../src/kilocode/tools/governor';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('Governor validation', () => {
  const tempDir = path.join(__dirname, 'tmp');

  beforeAll(async () => {
    await fs.mkdir(tempDir, { recursive: true });
    const manifest = {
      name: 'TestProject',
      lifecycle: 'production',
      dangerZones: ['api/real-money/'],
    };
    await fs.writeFile(path.join(tempDir, 'project.manifest.json'), JSON.stringify(manifest));
  });

  afterAll(async () => {
    await fs.rm(tempDir, { recursive: true, force: true });
  });

  test('blocks dangerous operation', async () => {
    const context = await loadProjectContext(tempDir);
    const result = validateOperation(context, 'api/real-money/transfer');
    expect(result.allowed).toBe(false);
    expect(result.ttsNarration).toBeDefined();
  });

  test('allows safe operation', async () => {
    const context = await loadProjectContext(tempDir);
    const result = validateOperation(context, 'api/health/check');
    expect(result.allowed).toBe(true);
  });
});
