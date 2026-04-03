import { DefaultAzureCredential } from '@azure/identity';
import { BlobServiceClient } from '@azure/storage-blob';
import { OpenAI } from 'openai';
import { InferenceSH } from '@inferencesh/sdk';

let _credential: DefaultAzureCredential | null = null;

export function getAzureCredential(): DefaultAzureCredential {
  if (!_credential) {
    _credential = new DefaultAzureCredential();
  }
  return _credential;
}

export function getBlobServiceClient(accountUrl: string): BlobServiceClient {
  return new BlobServiceClient(accountUrl, getAzureCredential());
}

export function getOpenAIClient(endpoint: string, apiKey: string): OpenAI {
  return new OpenAI({
    baseURL: endpoint,
    apiKey,
  });
}

export function getInferenceSHClient(apiKey: string): InferenceSH {
  return new InferenceSH({ apiKey });
}
