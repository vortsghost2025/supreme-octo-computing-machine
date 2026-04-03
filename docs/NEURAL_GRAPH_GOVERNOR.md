# Neural Graph Governor

## Overview

The Governor is a safety and policy enforcement layer for the SNAC-v2 agent system. It validates operations against project-specific danger zones, provides cross-project guidance, and generates TTS-friendly narrations for agent actions.

## Installation

All dependencies are already installed in `kilocode/packages/opencode`:

```bash
cd kilocode/packages/opencode
npm install
```

Dependencies include:
- `@kilocode/sdk` — Kilo runtime client
- `@azure/identity`, `@azure/storage-blob` — Azure SDK
- `openai` — OpenAI client
- `@inferencesh/sdk` — Inference.sh SDK
- `jest`, `ts-jest`, `@types/jest`, `typescript` — Testing

## Registration

Import and register the Governor early in your agent bootstrap:

```typescript
import { registerGovernor } from './kilocode';

// At startup
const registration = await registerGovernor(process.cwd());
console.log(`Governor registered. Server: ${registration.server.url}`);
console.log(`Project: ${registration.context?.name}`);
```

To unregister (e.g., on shutdown):

```typescript
import { unregisterGovernor } from './kilocode';
await unregisterGovernor();
```

## Exported Tools

| Tool | Signature | Description |
|------|-----------|-------------|
| `governor_load_context` | `(projectRoot: string) => ProjectContext` | Loads project manifest and returns context |
| `governor_validate` | `(context: ProjectContext, operationPath: string) => ValidationResult` | Validates path against danger zones |
| `governor_search` | `(query: string) => LibraryEntry[]` | Searches Neural-Graph library index |
| `governor_guidance` | `(projectName: string) => ProjectGuidance` | Gets cross-project guidance from registry |
| `governor_narrate` | `(message: string) => string` | Generates SSML-wrapped TTS narration |
| `governor_refresh` | `(projectRoot: string) => ProjectContext` | Refreshes cached context and clears caches |

## Usage Examples

### Validate an operation

```typescript
import { loadProjectContext, validateOperation } from './kilocode';

const context = await loadProjectContext('/path/to/project');
const result = validateOperation(context, '/backend/secrets.env');

if (!result.allowed) {
  console.log(result.reason);
  console.log(result.ttsNarration);
}
```

### Search the library

```typescript
import { searchLibrary } from './kilocode';

const results = await searchLibrary('authentication');
// Returns LibraryEntry[] with title, snippet, tags, relevance
```

### Get cross-project guidance

```typescript
import { getCrossProjectGuidance } from './kilocode';

const guidance = await getCrossProjectGuidance('my-other-project');
console.log(guidance.dangerZones);
console.log(guidance.notes);
```

### Generate TTS narration

```typescript
import { generateNarration } from './kilocode';

const ssml = generateNarration('Operation blocked: accessing danger zone.');
// Returns SSML-wrapped string ready for Azure TTS or other synthesizers
```

## Project Manifest

Create `project.manifest.json` in your project root:

```json
{
  "name": "my-project",
  "lifecycle": "production",
  "dangerZones": ["/backend/secrets", "/.env", "/scripts/rotate"],
  "allowedImports": ["@azure/identity", "openai"]
}
```

## Project Registry

Create `.kilo/registry.json` for cross-project guidance:

```json
{
  "my-project": {
    "projectName": "my-project",
    "lifecycle": "production",
    "dangerZones": ["/backend/secrets"],
    "notes": ["Never modify secrets directly. Use key rotation."]
  }
}
```

## Library Index

Create `.kilo/library/index.json` for search:

```json
[
  {
    "id": "auth-001",
    "title": "Azure AD Authentication",
    "snippet": "Use DefaultAzureCredential for managed identity auth...",
    "tags": ["azure", "auth", "identity"],
    "relevance": 0.95
  }
]
```

## Azure Integration

The Governor includes an Azure credential helper for policy-as-code extensions:

```typescript
import { getAzureCredential, getBlobServiceClient } from './kilocode/azure';

const cred = getAzureCredential();
const blobClient = getBlobServiceClient('https://myaccount.blob.core.windows.net');
```

## Testing

```bash
cd kilocode/packages/opencode
npm test
```

## CI

GitHub Actions runs tests on every push and PR. See `.github/workflows/ci.yml`.
