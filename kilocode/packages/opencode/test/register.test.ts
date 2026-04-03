import { registerGovernor, getRegistration, unregisterGovernor } from '../src/kilocode/register';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('Governor registration', () => {
  const tmpDir = path.join(__dirname, 'tmpReg');

  beforeAll(async () => {
    await fs.mkdir(tmpDir, { recursive: true });
    const manifest = {
      name: 'RegTestProject',
      lifecycle: 'dev',
      dangerZones: ['secret/'],
    };
    await fs.writeFile(path.join(tmpDir, 'project.manifest.json'), JSON.stringify(manifest));
    await registerGovernor(tmpDir);
  });

  afterAll(async () => {
    await unregisterGovernor();
    await fs.rm(tmpDir, { recursive: true, force: true });
  });

  test('registration object has client and tools', () => {
    const reg = getRegistration();
    expect(reg).toBeDefined();
    expect(reg?.client).toBeDefined();
    const names = reg?.tools.map(t => t.name) ?? [];
    expect(names).toContain('governor_load_context');
    expect(names).toContain('governor_validate');
    const loadTool = reg?.tools.find(t => t.name === 'governor_load_context');
    const validateTool = reg?.tools.find(t => t.name === 'governor_validate');
    expect(typeof loadTool?.handler).toBe('function');
    expect(typeof validateTool?.handler).toBe('function');
  });
});
