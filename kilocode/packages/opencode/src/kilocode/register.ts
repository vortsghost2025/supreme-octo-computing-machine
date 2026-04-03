let createKilo: any;
let createKiloClient: any;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const sdk = require('@kilocode/sdk');
  createKilo = sdk.createKilo;
  createKiloClient = sdk.createKiloClient;
} catch (e) {
  // Fallback stub for environments without the real SDK (e.g., unit tests)
  createKilo = async () => ({ client: {}, server: { url: 'http://localhost', close: () => {} } });
  createKiloClient = () => ({});
}

import {
  loadProjectContext,
  validateOperation,
  searchLibrary,
  getCrossProjectGuidance,
  generateNarration,
  refreshContext,
  type ProjectContext,
  type ValidationResult,
} from './tools/governor';

export interface GovernorTool {
  name: string;
  description: string;
  handler: (...args: any[]) => any;
}

export const governorTools: GovernorTool[] = [
  {
    name: 'governor_load_context',
    description: 'Load project context including name, lifecycle phase, danger zones, and allowed imports.',
    handler: loadProjectContext,
  },
  {
    name: 'governor_validate',
    description: 'Validate an operation path against project danger zones. Returns allowed status and TTS narration.',
    handler: validateOperation,
  },
  {
    name: 'governor_search',
    description: 'Search the Neural-Graph library index for code patterns and solutions.',
    handler: searchLibrary,
  },
  {
    name: 'governor_guidance',
    description: 'Get cross-project guidance from the unified project registry.',
    handler: getCrossProjectGuidance,
  },
  {
    name: 'governor_narrate',
    description: 'Generate TTS-optimised narration for a message.',
    handler: generateNarration,
  },
  {
    name: 'governor_refresh',
    description: 'Refresh cached project context and invalidate stale data.',
    handler: refreshContext,
  },
];

export interface GovernorRegistration {
  client: ReturnType<typeof createKiloClient>;
  server: { url: string; close(): void };
  tools: GovernorTool[];
  context: ProjectContext | null;
}

let _registration: GovernorRegistration | null = null;

export async function registerGovernor(projectRoot: string): Promise<GovernorRegistration> {
  if (_registration) {
    return _registration;
  }

  const { client, server } = await createKilo();

  let context: ProjectContext | null = null;
  try {
    context = await loadProjectContext(projectRoot);
  } catch {
    // ignore – defaults will be used
  }

  _registration = { client, server, tools: governorTools, context };
  return _registration;
}

export function getRegistration(): GovernorRegistration | null {
  return _registration;
}

export async function unregisterGovernor(): Promise<void> {
  if (_registration) {
    _registration.server.close();
    _registration = null;
  }
}

export {
  loadProjectContext,
  validateOperation,
  searchLibrary,
  getCrossProjectGuidance,
  generateNarration,
  refreshContext,
  type ProjectContext,
  type ValidationResult,
};
