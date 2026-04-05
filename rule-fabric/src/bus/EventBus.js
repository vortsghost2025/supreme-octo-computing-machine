import { EventEmitter } from 'events';
export class EventBus {
    static instance;
    emitter = new EventEmitter();
    constructor() { }
    static get() {
        if (!EventBus.instance)
            EventBus.instance = new EventBus();
        return EventBus.instance;
    }
    publish(event) {
        this.emitter.emit(event.type, event);
    }
    subscribe(type, listener) {
        this.emitter.on(type, listener);
    }
}
