import yaml from 'js-yaml';
import fs from 'fs';
import path from 'path';
export class RuleParser {
    static load(file) {
        const raw = fs.readFileSync(path.resolve(__dirname, '../../definitions', file), 'utf8');
        const doc = yaml.load(raw);
        return (doc.rules || []);
    }
}
