// TODO: This is a stub implementation — needs full implementation
// WarmStore: Disk-backed persistent cache with LRU eviction

class WarmStore {
  constructor(options = {}) {
    this.storagePath = options.storagePath || './data/warm';
    this.maxSizeMB = options.maxSizeMB || 500;
    this.store = new Map();
    this.accessOrder = [];
    this.metrics = { reads: 0, writes: 0, evictions: 0 };
  }

  async get(key) {
    this.metrics.reads++;
    const entry = this.store.get(key);
    if (entry) {
      this._updateAccessOrder(key);
      return entry.value;
    }
    return null;
  }

  async set(key, value) {
    this.metrics.writes++;
    this.store.set(key, { value, timestamp: Date.now() });
    this._updateAccessOrder(key);
  }

  async delete(key) {
    const idx = this.accessOrder.indexOf(key);
    if (idx > -1) this.accessOrder.splice(idx, 1);
    return this.store.delete(key);
  }

  async persist() {
    // TODO: flush to disk
  }

  async restore() {
    // TODO: load from disk
  }

  getStats() {
    return { ...this.metrics, size: this.store.size };
  }

  _updateAccessOrder(key) {
    const idx = this.accessOrder.indexOf(key);
    if (idx > -1) this.accessOrder.splice(idx, 1);
    this.accessOrder.push(key);
  }
}

module.exports = WarmStore;
