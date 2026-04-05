import yaml from 'js-yaml';
import { fileURLToPath } from 'url';
import fs from 'fs';
import path from 'path';

export interface Condition {
  field: string;
  op: '==' | '!=' | '>' | '>=' | '<' | '<=' | 'in' | 'contains';
  value: unknown;
}

export interface Action {
  type: string;
  params?: Record<string, unknown>;
}

export interface Rule {
  id: string;
  description?: string;
  when: Condition[];
  then: Action[];
}

export class RuleParser {
  static load(file: string): Rule[] {
    const filePath = path.resolve(__dirname, '../../definitions', file);
    const raw = fs.readFileSync(filePath, 'utf8');
    const doc = yaml.load(raw) as any;
    return (doc.rules || []) as Rule[];
  }
}
