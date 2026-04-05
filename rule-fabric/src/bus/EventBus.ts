import { EventEmitter } from 'events';

export interface EventEnvelope<T = any> {
  id: string;
  type: string;
  ts: number;
  source: string;
  payload: T;
  meta?: Record<string, unknown>;
}

export class EventBus {
  private static instance: EventBus;
  private emitter = new EventEmitter();

  private constructor() {}

  static get(): EventBus {
    if (!EventBus.instance) EventBus.instance = new EventBus();
    return EventBus.instance;
  }

  publish<T>(event: EventEnvelope<T>) {
    this.emitter.emit(event.type, event);
  }

  subscribe<T>(type: string, listener: (e: EventEnvelope<T>) => void) {
    this.emitter.on(type, listener);
  }
}
