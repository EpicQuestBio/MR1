import test from 'node:test';
import assert from 'node:assert/strict';
import { SignalHistory, EventDetector, MR1Stream, makeMR1Frame } from '../src/signal.js';

test('binary little endian protocol decodes bridge timestamp and float32 pA', () => {
  const stream = new MR1Stream({ sampleRate: 100000, bufferSeconds: 1 });
  const packet = makeMR1Frame(1234567890123n, [120.5, -44.25, 99.125]);
  stream.ingestPacket(packet);
  assert.equal(stream.lastTimestampUs, 1234567890123n);
  assert.equal(stream.history.get(0), 120.5);
  assert.equal(stream.history.get(1), -44.25);
  assert.equal(stream.received, 3);
});

test('timestamp gaps are represented by missing samples', () => {
  const stream = new MR1Stream({ bufferSeconds: 1 });
  stream.ingestPacket(makeMR1Frame(0n, [1, 2, 3, 4]));
  stream.ingestPacket(makeMR1Frame(60n, [9, 10]));
  assert.equal(stream.history.nextIndex, 8);
  assert.ok(Number.isNaN(stream.history.get(4)));
  assert.ok(Number.isNaN(stream.history.get(5)));
  assert.equal(stream.history.get(6), 9);
  assert.equal(stream.lost, 2);
});

test('32-bit microsecond timestamp rollover survives the bridge', () => {
  const stream = new MR1Stream({ bufferSeconds: 1 });
  stream.ingestPacket(makeMR1Frame(4294967276n, [5, 6]));
  stream.ingestPacket(makeMR1Frame(0n, [7, 8]));
  assert.equal(stream.received, 4);
  assert.equal(stream.history.nextIndex, 4);
});

test('min max summaries retain 2 sample events at far zoom and wrap correctly', () => {
  const history = new SignalHistory(100, 1);
  for (let i = 0; i < 100; i++) history.append(i === 29 || i === 30 ? 60 : 100);
  assert.deepEqual(history.range(0, 100), { min: 60, max: 100 });
  assert.deepEqual(history.range(28, 31), { min: 60, max: 100 });
  for (let i = 0; i < 100; i++) history.append(110);
  assert.equal(history.oldestIndex, 100);
  assert.deepEqual(history.range(100, 200), { min: 110, max: 110 });
  assert.ok(Number.isNaN(history.get(30)));
});

test('event detector records exactly 2-sample downward blockades', () => {
  const detector = new EventDetector(20, 2);
  for (let i = 0; i < 100; i++) detector.ingest(120, i);
  detector.ingest(89, 100);
  detector.ingest(90, 101);
  const event = detector.ingest(120, 102);
  assert.equal(event.startSample, 100);
  assert.equal(event.durationSamples, 2);
  assert.equal(detector.total, 1);
});

test('malformed and overlapping frames are rejected or ignored', () => {
  const stream = new MR1Stream({ bufferSeconds: 1 });
  assert.throws(() => stream.ingestPacket(new ArrayBuffer(9)), /Expected/);
  stream.ingestPacket(makeMR1Frame(100n, [1, 2, 3]));
  assert.equal(stream.ingestPacket(makeMR1Frame(110n, [3, 4])).ignored, true);
  assert.equal(stream.history.nextIndex, 3);
});

test('pyramid downsampling min/max fidelity across multiresolution tiers (16, 256, 4096)', () => {
  const history = new SignalHistory(10000, 2);
  const totalSamples = 8192;
  const raw = new Float32Array(totalSamples);
  for (let i = 0; i < totalSamples; i++) {
    // Generate pseudo-random baseline around 1200 pA
    const val = 1200 + Math.sin(i * 0.05) * 50;
    raw[i] = val;
    history.append(val);
  }

  // Inject a 2-sample sharp blockade dip at index 1024
  raw[1024] = 300.0;
  raw[1025] = 310.0;
  history.samples[1024] = 300.0;
  history.samples[1025] = 310.0;
  // Re-append to ensure pyramid summaries are updated correctly
  const testHist = new SignalHistory(10000, 2);
  for (let i = 0; i < totalSamples; i++) {
    let v = 1200 + Math.sin(i * 0.05) * 50;
    if (i === 1024) v = 300.0;
    if (i === 1025) v = 310.0;
    testHist.append(v);
  }

  // Query tier 1: small window (16 samples) containing the event
  const range16 = testHist.range(1020, 1036);
  assert.ok(range16);
  assert.equal(range16.min, 300.0);

  // Query tier 2: medium window (256 samples) containing the event
  const range256 = testHist.range(1000, 1256);
  assert.ok(range256);
  assert.equal(range256.min, 300.0);

  // Query tier 3: full 4096-block overview
  const range4096 = testHist.range(0, 4096);
  assert.ok(range4096);
  assert.equal(range4096.min, 300.0);

  // Verify non-event segment matches raw computation
  let expectedMin = Infinity, expectedMax = -Infinity;
  for (let i = 2000; i < 3000; i++) {
    const v = testHist.get(i);
    if (v < expectedMin) expectedMin = v;
    if (v > expectedMax) expectedMax = v;
  }
  const summaryRange = testHist.range(2000, 3000);
  assert.ok(summaryRange);
  assert.ok(Math.abs(summaryRange.min - expectedMin) < 1e-4);
  assert.ok(Math.abs(summaryRange.max - expectedMax) < 1e-4);
});

test('timestamp continuity: chronological insertion and zero/negative delta handling', () => {
  const stream = new MR1Stream({ bufferSeconds: 2 });
  // Initial frame at 1,000,000 us (1 second) with 4 samples
  const r1 = stream.ingestPacket(makeMR1Frame(1000000n, [100, 101, 102, 103]));
  assert.equal(r1.samples, 4);

  // Negative delta (older timestamp) -> should be rejected/ignored
  const rOlder = stream.ingestPacket(makeMR1Frame(999900n, [90, 91]));
  assert.equal(rOlder.ignored, true);
  assert.equal(stream.received, 4);

  // Zero delta (duplicate timestamp) -> should be rejected/ignored
  const rDup = stream.ingestPacket(makeMR1Frame(1000000n, [100, 101]));
  assert.equal(rDup.ignored, true);
  assert.equal(stream.received, 4);

  // Normal consecutive frame at 1,000,040 us (exactly 40 us = 4 samples later)
  const rNext = stream.ingestPacket(makeMR1Frame(1000040n, [104, 105, 106, 107]));
  assert.equal(rNext.samples, 4);
  assert.equal(stream.received, 8);
  assert.equal(stream.lost, 0);
  assert.equal(stream.history.nextIndex, 8);
});

test('transient detection across multi-scale events (2-sample, 5-sample, 50-sample)', () => {
  const detector = new EventDetector(25, 2);
  let sampleIdx = 0;

  // Initialize baseline around 1250 pA
  for (let i = 0; i < 150; i++) {
    detector.ingest(1250, sampleIdx++);
  }
  assert.ok(Math.abs(detector.baseline - 1250) < 1);

  // Event 1: 2-sample event (dwell time 20 us)
  const ev1Start = sampleIdx;
  detector.ingest(1000, sampleIdx++); // drop of 250 pA
  detector.ingest(1005, sampleIdx++);
  const ev1 = detector.ingest(1250, sampleIdx++); // recovery
  assert.ok(ev1, '2-sample event should be detected');
  assert.equal(ev1.startSample, ev1Start);
  assert.equal(ev1.durationSamples, 2);
  assert.ok(Math.abs(ev1.depthPA - 250) < 5);

  // Settle baseline
  for (let i = 0; i < 50; i++) detector.ingest(1250, sampleIdx++);

  // Event 2: 5-sample event (dwell time 50 us)
  const ev2Start = sampleIdx;
  for (let i = 0; i < 5; i++) {
    detector.ingest(950, sampleIdx++); // drop of 300 pA
  }
  const ev2 = detector.ingest(1250, sampleIdx++); // recovery
  assert.ok(ev2, '5-sample event should be detected');
  assert.equal(ev2.startSample, ev2Start);
  assert.equal(ev2.durationSamples, 5);
  assert.ok(Math.abs(ev2.depthPA - 300) < 5);

  // Settle baseline
  for (let i = 0; i < 50; i++) detector.ingest(1250, sampleIdx++);

  // Event 3: 50-sample event (dwell time 500 us)
  const ev3Start = sampleIdx;
  for (let i = 0; i < 50; i++) {
    detector.ingest(800, sampleIdx++); // drop of 450 pA
  }
  const ev3 = detector.ingest(1250, sampleIdx++); // recovery
  assert.ok(ev3, '50-sample event should be detected');
  assert.equal(ev3.startSample, ev3Start);
  assert.equal(ev3.durationSamples, 50);
  assert.ok(Math.abs(ev3.depthPA - 450) < 5);

  assert.equal(detector.total, 3);
});

test('telemetry JSON parsing and state management in MR1Stream', () => {
  const stream = new MR1Stream();
  assert.equal(stream.telemetry.weep_leak_detected, false);

  const tObj = {
    type: 'telemetry',
    timestamp: 1727731200.123,
    bias_mv: 250.0,
    temperature_c: 24.85,
    cis_pressure_psi: 2.45,
    trans_pressure_psi: 0.82,
    weep_leak_detected: true,
    flow_rate_cis_ul_min: 15.0
  };

  const parsed = stream.ingestTelemetry(JSON.stringify(tObj));
  assert.ok(parsed);
  assert.equal(stream.telemetry.bias_mv, 250.0);
  assert.equal(stream.telemetry.temperature_c, 24.85);
  assert.equal(stream.telemetry.weep_leak_detected, true);
  assert.equal(stream.telemetry.cis_pressure_psi, 2.45);

  // Ingest non-telemetry should return null and not overwrite
  assert.equal(stream.ingestTelemetry(JSON.stringify({ type: 'other' })), null);
  assert.equal(stream.telemetry.weep_leak_detected, true);
});
