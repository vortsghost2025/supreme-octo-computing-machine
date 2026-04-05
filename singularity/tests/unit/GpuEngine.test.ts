import { GpuEngine } from '../../src/gpu/GpuEngine';
import { execSync } from 'child_process';

describe('GpuEngine', () => {
  const hasNvcc = (() => {
    try {
      execSync('nvcc --version', { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  })();

  (hasNvcc ? test : test.skip)('compiles and runs hello kernel', async () => {
    const engine = new GpuEngine();
    const output = await engine.runKernel('hello');
    expect(output).toMatch(/Hello from GPU kernel/);
  });
});
