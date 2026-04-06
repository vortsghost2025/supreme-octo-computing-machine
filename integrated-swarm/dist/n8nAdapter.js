import { exec } from 'child_process';
import { promisify } from 'util';
import { writeFile } from 'fs/promises';
import { v4 as uuidv4 } from 'uuid';
const execAsync = promisify(exec);
/**
 * Pull a workflow from n8n instance.
 * Returns the raw JSON string.
 */
export async function pullWorkflow(id) {
    const { stdout } = await execAsync(`n8nac pull ${id}`);
    return stdout.trim();
}
/**
 * Validate a workflow JSON string against n8n schema.
 * Returns true if validation passes.
 */
export async function validateWorkflow(jsonContent) {
    const tempPath = `./tmp-${uuidv4()}.json`;
    await writeFile(tempPath, jsonContent);
    try {
        const { stdout } = await execAsync(`n8nac validate ${tempPath}`);
        return stdout.includes('Validation succeeded');
    }
    catch (_) {
        return false;
    }
    finally {
        // cleanup
        await execAsync(`rm -f ${tempPath}`);
    }
}
/**
 * Push a workflow JSON string to n8n.
 */
export async function pushWorkflow(id, jsonContent) {
    const tempPath = `./tmp-${uuidv4()}.json`;
    await writeFile(tempPath, jsonContent);
    await execAsync(`n8nac push ${id} ${tempPath}`);
    await execAsync(`rm -f ${tempPath}`);
}
/**
 * Run a dry‑run execution of a workflow.
 * Returns true if the dry‑run completes without error.
 */
export async function runDry(id) {
    try {
        const { stdout } = await execAsync(`n8nac run ${id} --dry-run`);
        return stdout.includes('Execution succeeded');
    }
    catch (_) {
        return false;
    }
}
