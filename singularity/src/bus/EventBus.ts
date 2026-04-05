export { EventBus } from '../../../rule-fabric/dist/bus/EventBus.js';

export interface EventEnvelope<T = any> {
  id: string;
  type: string;
  ts: number;
  source: string;
  payload: T;
  meta?: Record<string, unknown>;
}
