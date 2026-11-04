// MR1 waveform storage, protocol decoding, and optional simple event detector.
// No external dependencies. All sample times are measured from frame timestamps,
// never from WebSocket arrival time.

export const SAMPLE_RATE = 100_000;
export const SAMPLE_PERIOD_US = 1_000_000 / SAMPLE_RATE;
export const BUFFER_SECONDS = 60;

export class SignalHistory {
  constructor(sampleRate = SAMPLE_RATE, bufferSeconds = BUFFER_SECONDS) {
    this.sampleRate = sampleRate;
    this.capacity = Math.round(sampleRate * bufferSeconds);
    this.samples = new Float32Array(this.capacity);
    this.nextIndex = 0;
    // Small summaries can be combined to query any pixel range efficiently.
    this.levels = [16, 256, 4096].map(size => {
      const slots = Math.ceil(this.capacity / size) + 2;
      const ids = new Float64Array(slots);
      const min = new Float32Array(slots);
      const max = new Float32Array(slots);
      ids.fill(-1);
      min.fill(Infinity);
      max.fill(-Infinity);
      return { size, slots, ids, min, max };
    });
  }

  get oldestIndex() { return Math.max(0, this.nextIndex - this.capacity); }
  get availableSamples() { return this.nextIndex - this.oldestIndex; }

  append(value) {
    const index = this.nextIndex++;
    this.samples[index % this.capacity] = value;
    for (const level of this.levels) {
      const block = Math.floor(index / level.size);
      const slot = block % level.slots;
      if (level.ids[slot] !== block) {
        level.ids[slot] = block;
        level.min[slot] = Infinity;
        level.max[slot] = -Infinity;
      }
      if (Number.isFinite(value)) {
        if (value < level.min[slot]) level.min[slot] = value;
        if (value > level.max[slot]) level.max[slot] = value;
      }
    }
    return index;
  }

  get(index) {
    if (!Number.isInteger(index) || index < this.oldestIndex || index >= this.nextIndex) return NaN;
    return this.samples[index % this.capacity];
  }

  // Inclusive start, exclusive end. NaN represents a sample gap.
  range(start, end) {
    start = Math.max(this.oldestIndex, Math.floor(start));
    end = Math.min(this.nextIndex, Math.ceil(end));
    let lo = Infinity, hi = -Infinity;
    let pos = start;
    while (pos < end) {
      let consumed = false;
      for (let j = this.levels.length - 1; j >= 0; j--) {
        const level = this.levels[j];
        const size = level.size;
        if (pos % size !== 0 || pos + size > end) continue;
        const block = Math.floor(pos / size);
        const slot = block % level.slots;
        if (level.ids[slot] !== block) continue;
        if (level.min[slot] < lo) lo = level.min[slot];
        if (level.max[slot] > hi) hi = level.max[slot];
        pos += size;
        consumed = true;
        break;
      }
      if (!consumed) {
        const value = this.get(pos++);
        if (Number.isFinite(value)) {
          if (value < lo) lo = value;
          if (value > hi) hi = value;
        }
      }
    }
    return lo <= hi ? { min: lo, max: hi } : null;
  }
}

export class EventDetector {
  constructor(thresholdPA = 20, minSamples = 2) {
    this.thresholdPA = thresholdPA;
    this.minSamples = minSamples;
    this.baseline = null;
    this.active = null;
    this.total = 0;
    this.events = [];
    this.maxEvents = 6000;
  }

  resetTransient() { this.active = null; }

  ingest(value, sampleIndex) {
    if (!Number.isFinite(value)) {
      this.active = null;
      return null;
    }
    if (this.baseline === null) { this.baseline = value; return null; }
    const depth = this.baseline - value;
    if (this.active !== null) {
      if (depth >= this.thresholdPA * 0.45) {
        this.active.durationSamples++;
        if (value < this.active.minPA) this.active.minPA = value;
        if (depth > this.active.depthPA) this.active.depthPA = depth;
        return null;
      }
      const finished = this.active;
      this.active = null;
      this.baseline += 0.003 * (value - this.baseline);
      if (finished.durationSamples >= this.minSamples) {
        this.total++;
        this.events.push(finished);
        if (this.events.length > this.maxEvents) this.events.splice(0, this.events.length - this.maxEvents);
        return finished;
      }
      return null;
    }
    if (depth >= this.thresholdPA) {
      this.active = {
        startSample: sampleIndex,
        durationSamples: 1,
        baselinePA: this.baseline,
        minPA: value,
        depthPA: depth,
      };
    } else {
      // Gated EMA follows drift but does not get pulled down by blockades.
      this.baseline += 0.003 * (value - this.baseline);
    }
    return null;
  }
}

export class MR1Stream {
  constructor({ sampleRate = SAMPLE_RATE, bufferSeconds = BUFFER_SECONDS, thresholdPA = 20 } = {}) {
    this.sampleRate = sampleRate;
    this.bufferSeconds = bufferSeconds;
    this.thresholdPA = thresholdPA;
    this.telemetry = {
      bias_mv: 200,
      temperature_c: 25.0,
      cis_pressure_psi: 0.0,
      trans_pressure_psi: 0.0,
      weep_leak_detected: false,
      flow_rate_cis_ul_min: 0.0,
      mean_baseline_pa: 0.0,
      rms_noise_pa: 0.0,
      packets_received: 0,
      packets_dropped: 0
    };
    this.reset();
  }

  reset() {
    this.history = new SignalHistory(this.sampleRate, this.bufferSeconds);
    this.detector = new EventDetector(this.thresholdPA);
    this.lastTimestampUs = null;
    this.previousFrameLength = 0;
    this.received = 0;
    this.lost = 0;
    this.packets = 0;
    this.resets = (this.resets || 0);
    this.latestPA = NaN;
  }

  ingestTelemetry(json) {
    if (typeof json === 'string') {
      try {
        json = JSON.parse(json);
      } catch {
        return null;
      }
    }
    if (!json || json.type !== 'telemetry') return null;
    this.telemetry = { ...this.telemetry, ...json };
    return this.telemetry;
  }

  ingestPacket(buffer) {
    if (!(buffer instanceof ArrayBuffer) || buffer.byteLength < 12 || (buffer.byteLength - 8) % 4 !== 0) {
      throw new Error('Expected 8-byte LE uint64 timestamp followed by float32 LE current samples.');
    }
    const data = new DataView(buffer);
    const timestampUs = data.getBigUint64(0, true);
    const n = (buffer.byteLength - 8) / 4;
    if (this.lastTimestampUs !== null) {
      let deltaUs = timestampUs - this.lastTimestampUs;
      // Source DAQ timestamps are uint32 microseconds; the bridge wraps them in uint64.
      if (deltaUs < 0n && deltaUs + 4294967296n > 0n && deltaUs + 4294967296n < 5000000n) {
        deltaUs += 4294967296n;
      }
      const distanceSamples = Math.round(Number(deltaUs) / SAMPLE_PERIOD_US);
      const gap = distanceSamples - this.previousFrameLength;
      if (distanceSamples <= 0 || gap < 0) {
        // Ignore duplicate/out-of-order or overlapping frames rather than shifting data.
        return { ignored: true, reason: 'non-monotonic timestamp' };
      }
      if (gap > this.sampleRate * 2) {
        // A new simulator session / disconnected stream: avoid allocating an enormous gap.
        this.resets++;
        this.reset();
      } else if (gap >= 1) {
        // Insert NaN missing sample gaps when delta exceeds the expected sample interval
        // to prevent drawing artificial line ramps across dropped packets.
        this.lost += gap;
        this.detector.resetTransient();
        for (let i = 0; i < gap; i++) this.history.append(NaN);
      }
    }
    for (let i = 0; i < n; i++) {
      const value = data.getFloat32(8 + 4 * i, true);
      const index = this.history.append(value);
      this.detector.ingest(value, index);
      this.latestPA = value;
    }
    this.packets++;
    this.received += n;
    this.lastTimestampUs = timestampUs;
    this.previousFrameLength = n;
    return { samples: n, timestampUs };
  }
}

// The local demonstration encodes real MR1-format binary frames, so it exercises
// the same decoder and renderer as an actual websocket_bridge.py connection.
export function makeMR1Frame(timestampUs, values) {
  const frame = new ArrayBuffer(8 + values.length * 4);
  const view = new DataView(frame);
  view.setBigUint64(0, BigInt(timestampUs), true);
  for (let i = 0; i < values.length; i++) view.setFloat32(8 + i * 4, values[i], true);
  return frame;
}
