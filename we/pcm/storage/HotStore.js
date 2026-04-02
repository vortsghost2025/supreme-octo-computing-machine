// TODO: This is a stub implementation — needs full implementation
// HotStore: In-memory cache layer for frequently accessed mesh data

class HotStore {
  constructor(options = {}) {
    this.maxSize = options.maxSize || 10000;
    this.ttlMs = options.ttlMs || 60000;
    this.store = new Map();
    this.metrics = { hits: 0, misses: 0, evictions: 0 };
  }

  async get(key) {
    const entry = this.store.get(key);
    if (!entry) {
      this.metrics.misses++;
      return null;
    }
    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.store.delete(key);
      this.metrics.misses++;
      return null;
    }
    this.metrics.hits++;
    return entry.value;
  }

  async set(key, value, ttlMs) {
    if (this.store.size >= this.maxSize) {
      this._evictOldest();
    }
    this.store.set(key, { value, timestamp: Date.now(), ttl: ttlMs || this.ttlMs });
  }

  async delete(key) {
    return this.store.delete(key);
  }

  async clear() {
    this.store.clear();
  }

  getStats() {
    return { ...this.metrics, size: this.store.size, maxSize: this.maxSize };
  }

  _evictOldest() {
    const oldest = this.store.keys().next().value;
    if (oldest) {
      this.store.delete(oldest);
      this.metrics.evictions++;
    }
  }
}

module.exports = HotStore;
