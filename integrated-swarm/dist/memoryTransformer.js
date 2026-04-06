import { v4 as uuidv4 } from 'uuid';
/**
 * Adds metadata (uuid, timestamp) to a JSON object before it is stored in the episodic memory.
 */
export function enrichMemoryRecord(record) {
    return {
        ...record,
        __id: uuidv4(),
        __ts: Date.now(),
    };
}
