import { BaseAdapter } from '../BaseAdapter';
import { exec } from 'child_process';
import { promisify } from 'util';
const execAsync = promisify(exec);
export class N8nAdapter extends BaseAdapter {
    async pull(id) {
        const { stdout } = await execAsync(`n8nac pull ${id}`);
        return JSON.parse(stdout);
    }
    async validate(proposal) {
        const tmp = `/tmp/${Date.now()}-${Math.random()}.json`;
        await import('fs').then(f => f.promises.writeFile(tmp, JSON.stringify(proposal)));
        try {
            await execAsync(`n8nac validate ${tmp}`);
            return { valid: true };
        }
        catch {
            return { valid: false, issues: ['schema validation failed'] };
        }
        finally {
            await execAsync(`rm -f ${tmp}`);
        }
    }
    async push(proposal) {
        const tmp = `/tmp/${Date.now()}-${Math.random()}.json`;
        await import('fs').then(f => f.promises.writeFile(tmp, JSON.stringify(proposal)));
        await execAsync(`n8nac push ${proposal.id} ${tmp}`);
        await execAsync(`rm -f ${tmp}`);
        return { pushed: true };
    }
    async dryRun(proposal) {
        const tmp = `/tmp/${Date.now()}-${Math.random()}.json`;
        await import('fs').then(f => f.promises.writeFile(tmp, JSON.stringify(proposal)));
        try {
            await execAsync(`n8nac run ${proposal.id} --dry-run`);
            return { success: true };
        }
        finally {
            await execAsync(`rm -f ${tmp}`);
        }
    }
}
