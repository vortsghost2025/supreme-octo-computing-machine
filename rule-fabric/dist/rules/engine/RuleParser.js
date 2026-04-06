import yaml from 'js-yaml';
import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';
export class RuleParser {
    static load(file) {
        const __filename = fileURLToPath(import.meta.url);
        const __dirname = path.dirname(__filename);
        const raw = fs.readFileSync(path.resolve(__dirname, '../../definitions', file), 'utf8');
        const doc = yaml.load(raw);
        return (doc.rules || []);
    }
}
