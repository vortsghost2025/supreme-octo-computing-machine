import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';
import fs from 'fs';

const execAsync = promisify(exec);

/**
 * Simple GPU engine wrapper for CUDA kernels.
 * It compiles .cu files with `nvcc` and runs the resulting binary.
 * Assumes `nvcc` is available in PATH (GTX 5060 environment).
 */
export class GpuEngine {
  private kernelDir: string;
  private buildDir: string;

  constructor(kernelDir = path.resolve(process.cwd(), 'kernels'), buildDir = path.resolve(process.cwd(), 'gpu_build')) {
    this.kernelDir = kernelDir;
    this.buildDir = buildDir;
    if (!fs.existsSync(this.buildDir)) {
      fs.mkdirSync(this.buildDir, { recursive: true });
    }
  }

  /** Compile a kernel by name (e.g., "hello" looks for kernels/hello.cu). */
  async compileKernel(name: string): Promise<string> {
    const src = path.join(this.kernelDir, `${name}.cu`);
    const out = path.join(this.buildDir, `${name}.out`);
    if (!fs.existsSync(src)) {
      throw new Error(`Kernel source not found: ${src}`);
    }
    const cmd = `nvcc -arch=sm_86 ${src} -o ${out}`;
    await execAsync(cmd);
    return out;
  }

  /** Run a compiled kernel, optionally passing CLI args. */
  async runKernel(name: string, args: string[] = []): Promise<string> {
    const exe = await this.compileKernel(name);
    const cmd = `${exe} ${args.join(' ')}`.trim();
    const { stdout } = await execAsync(cmd);
    return stdout;
  }
}
