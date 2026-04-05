import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

export class EpisodicStore {
  private base = path.resolve(process.cwd(), '.kilo', 'memory', 'episodic');
  constructor() {
    if (!fs.existsSync(this.base)) fs.mkdirSync(this.base, { recursive: true });
  }
  async append(record: Record<string, unknown>) {
    const line = JSON.stringify({ __id: uuidv4(), __ts: Date.now(), ...record }) + '\n';
    await fs.promises.appendFile(path.join(this.base, 'log.jsonl'), line);
  }
}
