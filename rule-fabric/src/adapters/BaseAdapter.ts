export abstract class BaseAdapter {
  abstract pull(id: string): Promise<unknown>;
  abstract validate(proposal: unknown): Promise<{ valid: boolean; issues?: string[] }>;
  abstract push(proposal: unknown): Promise<unknown>;
  abstract dryRun?(proposal: unknown): Promise<{ success: boolean }>;
}
