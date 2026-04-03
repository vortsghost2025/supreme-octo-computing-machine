import { v4 as uuidv4 } from 'uuid';

/**
 * Adds metadata (uuid, timestamp) to a JSON object before it is stored in the episodic memory.
 */
export function enrichMemoryRecord<T extends object>(record: T): T & { __id: string; __ts: number } {
  return {
    ...record,
    __id: uuidv4(),
    __ts: Date.now(),
  } as any;
}
